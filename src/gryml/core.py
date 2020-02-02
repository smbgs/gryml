import logging
import re
from datetime import datetime
from io import StringIO
from pathlib import Path

import sys
from jinja2 import Environment, TemplateSyntaxError
from ruamel.yaml import YAML
from ruamel.yaml.representer import RoundTripRepresenter

from ruamel.yaml.comments import CommentedMap, CommentedSeq, LineCol

from gryml.pipes import Pipes
from gryml.strategies import Strategies
from gryml.utils import SilentUndefined, deep_merge, LazyString

RoundTripRepresenter.add_representer(LazyString, RoundTripRepresenter.represent_str)


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
        self.active_rules_lines = set()

        self.context_values = {}

        self.sources = []

        # TODO: this needs to be adjustable from decorator
        self.skip_nested_processing_strats = {'repeat'}
        self.eager_strats = {'if', 'else', 'repeat', 'with', 'proto', 'extend'}

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
            self.logger.error(e)
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
            raise e

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
            before_values.pop('gryml', None)

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
                tags = self.extract_tags(rd)

                deep_merge(values, before_values)
                before_values.update(values)
                values = self.process(values, dict(tags=tags, values=before_values, mutable=mutable, path=path))
                #values = before_values

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

    def iterate_path(self, path: Path):

        if path == '-':
            input_rd = StringIO(sys.stdin.read())
            tags = self.extract_tags(input_rd)
            input_rd.seek(0)
            prd = self.yaml.load_all(input_rd)
            for rd in prd:
                yield path, rd, tags
            return

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        if path.is_file():
            with open(path) as rd:
                tags = self.extract_tags(rd)
                rd.seek(0)
                prd = self.yaml.load_all(rd)
                for rd in prd:
                    yield path, rd, tags

        elif path.is_dir():
            for sub_dir in path.iterdir():
                yield from self.iterate_path(sub_dir)

    def extract_tags(self, body):
        result_comments = {}
        for i, line in enumerate(body):
            matches = self.gryml_line_mask.search(line)
            if matches:
                line_start = matches.group(1) is not None
                matches = [it.groupdict() for it in self.gryml_mask.finditer(line[matches.regs[0][0]:]) if it.lastgroup]
                if matches:
                    line = i + 1
                    for it in matches:
                        it.update(line_start=line_start, line=line)
                    result_comments[line] = matches

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
            raise e

    def get_rules(self, target, context):

        line = context.get('line')
        parent_line = context.get('parent_line')
        tags = context.get('tags')

        rules = []
        comment = tags.get(line)
        if comment:

            # Skipping line comments for list items which are not also dicts
            if not context.get('is_list_item') or not isinstance(target, dict):
                if isinstance(target, CommentedMap):

                    if not target.lc.data:
                       rules.extend(comment)

                    elif list(target.lc.data.values())[0][0] != list(target.lc.data.values())[0][2] != target.lc.line:
                       rules.extend(comment)

                else:
                    rules.extend(comment)

        if parent_line != line:
            offset = 1
            above_comment = tags.get(line - offset)
            while above_comment and above_comment[0]['line_start']:
                for idx, rule in enumerate(above_comment):
                    rules.insert(idx, rule)
                offset += 1
                above_comment = tags.get(line - offset)

        rules = [rule for rule in rules if id(rule) not in self.active_rules_lines]
        return rules

    def apply_rules(self, target, context, rules):

        value = target

        context['value_used'] = True
        context['may_repeat'] = True
        context['rules'] = rules

        for rule in rules:
            if rule['strat'] is None:
                rule['strat'] = 'set'

            if id(rule) in self.active_rules_lines:
                continue

            self.active_rules_lines.add(id(rule))

            value = self.apply_strategy(rule['strat'], value, rule['arg_exp'], rule['exp'], context)
            self.active_rules_lines.remove(id(rule))

            if context.get('value_repeated'):
                break

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

        context.setdefault('proto', {})

        path = context.get('path') if context else None
        tags = context.get('tags', {}) if context else {}
        values = context.get('values', {}) if context else {}
        mutable = context.get('mutable', False) if context else False
        line = context.setdefault('line', 0) if context else 0

        rules = context.get('extra_rules', None) or self.get_rules(target, context)  # type: list

        result = self.apply_rules(target, context, [r for r in rules if r['strat'] in self.eager_strats])

        if not context['value_used'] or context.get('value_processed'):
            return result

        if context.get('value_repeated'):
            return self.apply_rules(result, context, [r for r in rules if r['strat'] not in self.eager_strats])

        target = result

        if isinstance(target, CommentedMap):
            result = CommentedMap()
            setattr(result, LineCol.attrib, target.lc)
            to_delete = set()
            for k, v in target.items():

                # TODO: something needs to be done with this case
                if not target.lc.data or k not in target.lc.data:
                    result[k] = v
                    continue

                ctx = {
                    'proto': context.get('proto', {}),
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
                context['proto'].update(ctx['proto'])
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

                # TODO: something needs to be done with this case
                if not target.lc.data or k not in target.lc.data:
                    result.append(v)
                    continue

                ctx = {
                    'proto': context.get('proto', {}),
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
                    context['proto'].update(ctx['proto'])
                else:
                    value = v

                if ctx['value_used'] and not ctx.get('value_repeated'):
                    if mutable:
                        target[k] = value
                    result.append(value)
            if mutable:
                target.clear()
                target.extend(result)

        base = context.get('base')

        result = self.apply_rules(result, context, [r for r in rules if r['strat'] not in self.eager_strats])

        if base:
            deep_merge(base, result)
            result.clear()
            result.update(base)

        return result

    def iterate_definitions(self, definition_file, values=None):

        if values is None:
            values = self.values

        for path, definition, tags in self.iterate_path(Path(definition_file)):
            yield self.process(definition, dict(tags=tags, values=values, path=path))

    def process_sources(self):

        def process_list(sources, nested_context):

            for source_path in sources:

                if source_path is None:
                    # Sometimes conditions may return None, so we'll just ignore such sources
                    continue

                context = self.context_values.get(id(source_path), {})

                if isinstance(source_path, dict):
                    nested_sources = source_path.get('output')
                    yield from process_list(nested_sources, context)
                    continue

                if source_path != '-':
                    source_path = self.path.parent.resolve() / source_path

                for sub_path, it, sub_tags in self.iterate_path(source_path):

                    result = self.process(it, dict(
                        tags=sub_tags,
                        values={**self.values, **context, **nested_context},
                        offset=it.lc.line,
                        mutable=False,
                        path=sub_path,
                    ))
                    self.output.write('---\n')
                    self.yaml.dump(result, self.output)
                    yield sub_path, result

        yield from process_list(self.sources, {})

    def process_first_definition(self, definition_file, values=None):
        if values is None:
            values = self.values
        return next(self.iterate_definitions(definition_file, values))

    def store_context_values(self, target, values):
        self.context_values[id(target)] = values

    def print(self, target):
        self.yaml.dump(target, self.output)

