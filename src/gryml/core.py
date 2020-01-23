import logging
import re
from datetime import datetime
from io import StringIO
from pathlib import Path

import sys
from jinja2 import Environment, TemplateSyntaxError
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq, LineCol

from gryml.pipes import Pipes
from gryml.strategies import Strategies
from gryml.utils import SilentUndefined, deep_merge


class Gryml:

    logger = logging.getLogger('Gryml:Core')

    gryml_pattern = r'(?:\[(?P<strat>[^]\s]+)(?:\s?(?P<arg_exp>[^]]+))?\])?(?:{(?P<exp>[^}]+)})?'
    gryml_mask = re.compile(rf'{gryml_pattern}')
    gryml_line_mask = re.compile(r'(?P<line_start>^[\s]*)?#[\[\{]', flags=re.MULTILINE)

    sub_pattern = re.compile(rf"\$\((?:([a-zA-Z][a-zA-Z0-9._]*))\)")

    def __init__(self, output=None):
        self.values = {}
        self.output = output or StringIO()
        self.env = Environment(undefined=SilentUndefined)
        self.yaml = YAML(typ=['safe', 'rt'])
        self.path = Path('.')

        self.context_values = {}

        self.sources = []

        # TODO: this needs to be adjustable from decorator
        self.skip_nested_processing_strats = {'repeat'}

        for name, pipe in Pipes.pipes.items():

            def wrapper(p):
                return lambda *x: p(*x, self)

            self.env.filters[name] = wrapper(pipe)

        self.env.globals['semstamp'] = lambda r: datetime.utcnow().strftime(f'{r}.%Y%m.%d-%H%M')
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True

    def resolve(self, path):
        return self.path.parent.resolve() / path

    def set_values(self, values):
        self.values = values

    def update_values(self, values):
        self.values.update(values)

    def template(self, template, context=None, **kwargs):
        try:
            compiled = self.env.from_string(template)
            return compiled.render(self.normalize_values({
                **self.values,
                **context.get('values', {}),
                **kwargs
            }))
        except TemplateSyntaxError as e:

            self.logger.error(
                "Unable to compile the template\n"
                "Reason: %s\n"
                "Template line: %s\n"
                "Line: %s",
                e.message,
                e.lineno,
                context.get('line', 0) + e.lineno
            )
            raise e
        except Exception as e:
            # TODO: handle logging properly
            self.logger.exception(e)
            raise e

    def eval(self, expression, context=None, **kwargs):

        if context is None:
            context = {}

        self.env.filters['s'] = \
            lambda s: self.sub_pattern.sub(lambda mo: str(self.eval(mo.group(1), context)), s)

        try:
            return self.env.compile_expression(expression, undefined_to_none=False)(self.normalize_values({
                **self.values,
                **context.get('values', {}),
                **kwargs
            }))
        except Exception as e:
            self.logger.error(
                "Unable evaluate expression: `%s`\n"
                "Reason: %s\n"
                "File: %s (line: %s)\n",
                expression,
                e,
                Path(context.get('path')).resolve() if context.get('path') else '<undefined>',
                context.get('line'),
                )

    @staticmethod
    def parse_values(source_values):
        values = {}
        for it in source_values:
            k, v = it.split('=')
            value = values
            path = k.split('.')
            for c in path[:-1]:
                if c in value:
                    value = value[c]
                else:
                    value[c] = dict()
                    value = value[c]
            value[path[-1]] = v
        return values

    def load_values(self, path: Path, base_values=None, process=False, mutable=False,
                    load_nested=False, load_sources=False):

        if not path.exists():
            raise FileNotFoundError(path)

        if not path.is_file():
            return

        self.path = path

        with open(str(path)) as rd:
            self.yaml = YAML(typ=['safe', 'rt'])

            values = self.yaml.load(rd)
            rd.seek(0)
            before_values = base_values if base_values else {}

            gryml = values.get('gryml', {})
            loadable_before = gryml.get('include', [])

            if load_nested:
                for it in loadable_before:
                    nested_gryml = Gryml(self.output)
                    before_values.update(nested_gryml.load_values(
                        path.parent.resolve() / it, before_values, process, mutable, load_nested, load_sources)
                    )

                    self.sources.extend(nested_gryml.sources)
                    self.context_values.update(nested_gryml.context_values)

            if process:
                tags = self.extract_tags(rd, 0)

                deep_merge(values, before_values)
                before_values.update(values)
                self.process(values, dict(tags=tags, values=before_values, mutable=mutable, path=path))
                values = before_values

            loadable_after = gryml.get('override', [])
            loadable_sources = gryml.get('output', [])

            if load_nested:
                after_values = CommentedMap()
                for it in loadable_after:
                    nested_gryml = Gryml(self.output)
                    after_values.update(nested_gryml.load_values(
                        path.parent.resolve() / it, values, process, mutable, load_nested, load_sources
                    ))
                    loadable_sources.extend(nested_gryml.sources)
                    self.context_values.update(nested_gryml.context_values)

                values.update(after_values)

            if load_sources:
                self.sources.extend(loadable_sources)

            self.values = values

            return self.values

    @staticmethod
    def process_file(path, rd, prd, starting_pos):
        for it in prd:
            ending_pos = rd.tell()
            output = StringIO()
            rd.seek(starting_pos)
            output.write(rd.read(ending_pos - starting_pos))
            output.seek(0)
            yield path, output, it, starting_pos
            starting_pos = ending_pos

    def iterate_path(self, path: Path):

        if path == '-':
            input_rd = StringIO(sys.stdin.read())
            prd = self.yaml.load_all(input_rd)
            for it in self.process_file(path, input_rd, prd, 0):
                yield it
            return

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        if path.is_file():
            with open(path) as rd:
                stating_pos = rd.tell()
                prd = self.yaml.load_all(rd)
                for it in self.process_file(path, rd, prd, stating_pos):
                    yield it

        elif path.is_dir():
            for sub_dir in path.iterdir():
                for sub_path, output, it, stating_pos in self.iterate_path(sub_dir):
                    yield sub_path, output, it, stating_pos

    def extract_tags(self, body, offset):
        result_comments = {}
        for i, line in enumerate(body):
            matches = self.gryml_line_mask.search(line)
            if matches:
                line_start = matches.group(1) is not None
                matches = [it.groupdict() for it in self.gryml_mask.finditer(line[matches.regs[0][0]:]) if it.lastgroup]
                if matches:
                    for it in matches:
                        it.update(line_start=line_start)
                    result_comments[i + 1 + offset] = matches
        return result_comments

    def apply_strategy(self, name, old_value, strat_expression, value_expression, context):
        try:
            return Strategies.apply(name, self, old_value, strat_expression, value_expression, context)
        except Exception as e:
            self.logger.error(
                "Unable to apply the `%s` strategy while evaluating expression: `%s`\n"
                "Reason: %s\n"
                "File: %s (line: %s)\n",
                name,
                strat_expression or value_expression,
                e,
                Path(context.get('path')).resolve() if context.get('path') else '<undefined>',
                context.get('line'),
            )

    @staticmethod
    def get_rules(target, context):

        line = context.get('line')
        parent_line = context.get('parent_line')
        tags = context.get('tags')

        rules = []
        comment = tags.get(line)
        if comment:

            # Skipping line comments for list items which are not also dicts
            if not context.get('is_list_item') or not isinstance(target, dict):
                rules.extend(comment)

        if parent_line != line:
            offset = 1
            above_comment = tags.get(line - offset)
            while above_comment and above_comment[0]['line_start']:
                for idx, rule in enumerate(above_comment):
                    rules.insert(idx, rule)
                offset += 1
                above_comment = tags.get(line - offset)

        return rules

    def apply_rules(self, target, context, rules):

        value = target

        context['value_used'] = True
        context['may_repeat'] = True
        context['rules'] = rules

        for rule in rules:
            if rule['strat'] is None:
                rule['strat'] = 'set'

            value = self.apply_strategy(rule['strat'], value, rule['arg_exp'], rule['exp'], context)

        return value

    def normalize_values(self, values):
        if isinstance(values, dict):
            result = dict()
            for k, v in values.items():
                result[k] = self.normalize_values(v)
            return result

        elif isinstance(values, list):
            result = list()
            for v in values:
                result.append(self.normalize_values(v))
            return result
        else:
            return values

    def process(self, target, context=None):

        result = target

        path = context.get('path') if context else None
        tags = context.get('tags', {}) if context else {}
        values = context.get('values', {}) if context else {}
        mutable = context.get('mutable', False) if context else False
        line = context.setdefault('line', 0) if context else 0

        rules = self.get_rules(result, context)  # type: list

        if any(rule['strat'] in self.skip_nested_processing_strats for rule in rules):
            return self.apply_rules(result, context, rules)

        if isinstance(target, CommentedMap):
            result = CommentedMap()
            setattr(result, LineCol.attrib, target.lc)
            to_delete = set()
            for k, v in target.items():
                if not target.lc.data or k not in target.lc.data:
                    result[k] = v
                    continue

                ctx = {
                    'path': path,
                    'tags': tags,
                    'values': values,
                    'mutable': mutable,
                    'is_map_value': True,
                    'key': k,
                    'parent_line': line,
                    'line': target.lc.data[k][0] + 1,
                    'value_used': True
                }

                value = self.process(v, ctx)
                if ctx['value_used']:
                    result[k] = value
                    if mutable:
                        target[k] = value
                else:
                    to_delete.add(k)

            if mutable:
                target.update(result)
                for d in to_delete:
                    target.pop(d)

        elif isinstance(target, CommentedSeq):
            result = CommentedSeq()
            setattr(result, LineCol.attrib, target.lc)
            for k, v in enumerate(target):
                ctx = {
                    'path': path,
                    'tags': tags,
                    'values': values,
                    'mutable': mutable,
                    'is_list_item': True,
                    'list': result,
                    'index': k,
                    'parent_line': line,
                    'line': target.lc.data[k][0] + 1,
                    'value_used': True
                }

                # Only processing this iter value if it's not on the same string as parent definition
                if line != ctx['line']:
                    value = self.process(v, ctx)
                else:
                    value = v

                if mutable:
                    target[k] = v

                if ctx['value_used']:
                    result.append(value)
            if mutable:
                target.clear()
                target.extend(result)

        return self.apply_rules(result, context, rules)

    def iterate_definitions(self, definition_file, values=None):

        if values is None:
            values = self.values

        for path, body, definition, offset in self.iterate_path(Path(definition_file)):
            tags = self.extract_tags(body, offset)
            yield self.process(definition, dict(tags=tags, values=values, path=path))

    def process_sources(self):

        for source_path in self.sources:

            context = self.context_values.get(id(source_path), {})

            if isinstance(source_path, dict):
                source_path = source_path.pop('path')
                context = {**context, **source_path}

            if source_path != '-':
                source_path = self.path.parent.resolve() / source_path

            for sub_path, output, it, offset in self.iterate_path(source_path):
                sub_tags = self.extract_tags(output, offset)

                result = self.process(it, dict(
                    tags=sub_tags,
                    values={**context, **self.values},
                    offset=it.lc.line,
                    mutable=False,
                    path=sub_path,
                ))
                self.output.write('---\n')
                self.yaml.dump(result, self.output)
                yield sub_path, result

    def process_first_definition(self, definition_file, values=None):
        if values is None:
            values = self.values
        return next(self.iterate_definitions(definition_file, values))

    def store_context_values(self, target, values):
        self.context_values[id(target)] = values

    def print(self, target):
        self.yaml.dump(target, self.output)

