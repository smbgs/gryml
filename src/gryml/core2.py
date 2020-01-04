import random
import re
import string

import sys
from copy import copy, deepcopy
from io import StringIO
from pathlib import Path

from jinja2 import Environment, UndefinedError, Undefined
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq, LineCol

from gryml.strategies2 import Strategies
from string import Template


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

        # self.env.filters['s'] = \
        #     lambda s: self.sub_pattern.sub(lambda mo: self.eval(mo.group(1), {}), s)

    def set_values(self, values):
        self.values = values

    def eval(self, expression, context=None, **kwargs):

        self.env.filters['s'] = \
            lambda s: self.sub_pattern.sub(lambda mo: str(self.eval(mo.group(1), context)), s)

        return self.env.compile_expression(expression, undefined_to_none=False)({
            **self.values,
            **context.get('values', {}),
            **kwargs
        })

    def load_values(self, path: Path):

        if not path.exists():
            raise FileNotFoundError(path)

        if path.is_file():
            with open(path) as rd:
                self.yaml = YAML(typ=['safe', 'rt'])
                self.values = self.yaml.load(rd)

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

    def apply_strat(self, name, old_value, strat_expression, value_expression, context):
        return Strategies.apply(name, self, old_value, strat_expression, value_expression, context)

    def apply_value(self, target, tags, context):

        value = target

        line = context.get('line')

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

            value = self.apply_strat(rule['strat'], value, rule['arg_exp'], rule['exp'], context)

        return value

    def process(self, target, tags, offset, context=None):

        result = target

        if isinstance(target, dict):
            result = CommentedMap()
            setattr(result, LineCol.attrib, target.lc)
            for k, v in target.items():
                ctx = {
                    'values': context.get('values', {}) if context else {},
                    'is_map_value': True,
                    'key': k,
                    'line': target.lc.data[k][0],
                }
                value = self.process(v, tags, offset, ctx)
                if value is not None:
                    result[k] = value

        elif isinstance(target, list):
            result = CommentedSeq()
            setattr(result, LineCol.attrib, target.lc)
            for k, v in enumerate(target):
                ctx = {
                    'values': context.get('values', {}) if context else {},
                    'is_list_item': True,
                    'list': result,
                    'index': k,
                    'line': target.lc.data[k][0] if target.lc.data[k][0] != target.lc.line else None,
                }

                value = self.process(v, tags, offset, ctx)
                if value is not None:
                    result.append(value)

        if context and context.get('line'):
            return self.apply_value(result, tags, {
                **context,
                'tags': tags,
                'offset': offset,
                'line': context['line'] - offset + 1
            })
        else:
            return result

    def print(self, target):
        self.yaml.dump(target, sys.stdout)
