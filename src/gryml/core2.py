import random
import re
import string
from datetime import date, datetime
from io import StringIO
from pathlib import Path

import sys
from jinja2 import Environment, Undefined
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq, LineCol

from gryml.strategies2 import Strategies


class FriendlyUndefined(Undefined):

    def __getattr__(self, item):
        return self


class Gryml:
    gryml_pattern = r'(?:\[(?P<strat>[^]\s]+)(?:\s?(?P<arg_exp>[^]]+))?\])?(?:{(?P<exp>[^}]+)})?'
    gryml_mask = re.compile(rf'{gryml_pattern}')
    gryml_line_mask = re.compile(r'(?P<line_start>^[\s]*)?#[\[\{]', flags=re.MULTILINE)

    sub_pattern = re.compile(rf"\$\((?:([a-zA-Z][a-zA-Z0-9._]*))\)")

    def __init__(self):
        self.values = {}
        self.env = Environment(undefined=FriendlyUndefined)
        self.yaml = YAML(typ=['safe', 'rt'])

        # TODO: separate
        self.env.filters['randstr'] = \
            lambda n: ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(n))

        self.env.globals['semstamp'] = lambda r: datetime.utcnow().strftime(f'{r}.%Y%m.%d-%H%M')

    def set_values(self, values):
        self.values = values

    def eval(self, expression, context=None, **kwargs):

        if context is None:
            context = {}

        self.env.filters['s'] = \
            lambda s: self.sub_pattern.sub(lambda mo: str(self.eval(mo.group(1), context)), s)

        return self.env.compile_expression(expression, undefined_to_none=False)({
            **self.values,
            **context.get('values', {}),
            **kwargs
        })

    def load_values(self, path: Path, base_values=None, process=False, load_nested=False, load_sources=False):

        if not path.exists():
            raise FileNotFoundError(path)

        if not path.is_file():
            return

        with open(str(path)) as rd:
            self.yaml = YAML(typ=['safe', 'rt'])

            values = self.yaml.load(rd)
            rd.seek(0)
            before_values = CommentedMap(base_values if base_values else {})

            load_before = values.pop('$gryml-values-before', [])
            load_after = values.pop('$gryml-values-after', [])
            load_sources = values.pop('$gryml-sources', [])

            if load_nested:
                for it in load_before:
                    before_values.update(self.load_values(path.parent.resolve() / it, base_values, process, load_nested, load_sources))

            if process:
                tags = self.extract_tags(rd)
                before_values.update(values)
                values = self.process(values, dict(tags=tags, values=before_values, offset=0))
                before_values.update(values)
                values = before_values

            if load_nested:
                after_values = CommentedMap()
                for it in load_after:
                    after_values.update(self.load_values(path.parent.resolve() / it, values, process, load_nested, load_sources))

                values.update(after_values)

            return values

    def iterate_path(self, path: Path):

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        if path.is_file():
            with open(path) as rd:
                prd = self.yaml.load_all(rd)
                for it in prd:
                    output = StringIO()
                    self.yaml.dump(it, output)
                    output.seek(0)
                    yield path, output, it

        elif path.is_dir():
            for sub_dir in path.iterdir():
                for sub_path, output, it in self.iterate_path(sub_dir):
                    yield sub_path, output, it

    def extract_tags(self, body):
        result_comments = {}
        for i, line in enumerate(body):
            matches = self.gryml_line_mask.search(line)
            if matches:
                line_start = bool(matches.group(1))
                matches = [it.groupdict() for it in self.gryml_mask.finditer(line[matches.regs[0][0]:]) if it.lastgroup]
                if matches:
                    for it in matches:
                        it.update(line_start=line_start)
                    result_comments[i + 1] = matches
        return result_comments

    def apply_strategy(self, name, old_value, strat_expression, value_expression, context):
        return Strategies.apply(name, self, old_value, strat_expression, value_expression, context)

    def apply_value(self, target, context):

        value = target

        line = context.get('line')
        tags = context.get('tags')

        rules = []
        comment = tags.get(line)
        if comment:
            if not context.get('is_list_item') or not isinstance(target, dict):
                rules.extend(comment)

        offset = 1
        above_comment = tags.get(line - offset)
        while above_comment and above_comment[0]['line_start']:
            for idx, rule in enumerate(above_comment):
                rules.insert(idx, rule)
            offset += 1
            above_comment = tags.get(line - offset)

        context['value_used'] = True
        context['may_repeat'] = True

        context['rules'] = rules

        for rule in rules:
            if rule['strat'] is None:
                rule['strat'] = 'set'

            value = self.apply_strategy(rule['strat'], value, rule['arg_exp'], rule['exp'], context)

        return value

    def process(self, target, context=None):

        result = target
        tags = context.get('tags', {}) if context else {}
        values = context.get('values', {}) if context else {}
        offset = context.get('offset', 0) if context else 0
        mutable = context.get('mutable', False) if context else False

        if isinstance(target, dict):
            result = CommentedMap()
            setattr(result, LineCol.attrib, target.lc)
            for k, v in target.items():
                if not target.lc.data or k not in target.lc.data:
                    result[k] = v
                    continue

                ctx = {
                    'tags': tags,
                    'values': values,
                    'offset': offset,
                    'is_map_value': True,
                    'key': k,
                    'line': target.lc.data[k][0] - offset + 1,
                    'value_used': True
                }

                value = self.process(v, ctx)

                if mutable:
                    if ctx['value_used']:
                        result[k] = value
                        target[k] = value
                    else:
                        del target[k]
                else:
                    if ctx['value_used']:
                        result[k] = value

        elif isinstance(target, list):
            result = CommentedSeq()
            setattr(result, LineCol.attrib, target.lc)
            for k, v in enumerate(target):
                ctx = {
                    'tags': tags,
                    'values': values,
                    'offset': offset,
                    'is_list_item': True,
                    'list': result,
                    'index': k,
                    'line': target.lc.data[k][0] - offset + 1 if target.lc.data[k][0] != target.lc.line else None,
                    'value_used': True
                }

                value = self.process(v, ctx)
                if ctx['value_used']:
                    result.append(value)
            if mutable:
                target.clear()
                target.extend(result)

        if context and context.get('line'):
            return self.apply_value(result, context)
        else:
            return result

    def print(self, target):
        self.yaml.dump(target, sys.stdout)
