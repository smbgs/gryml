import logging
import re
import sys
from collections import OrderedDict
from pathlib import Path

from ruamel.yaml import YAML

from gryml.pipes import Pipes
from gryml.strategies import Strategies
from gryml.utils import print_warning

pipe_mask = r'(?:\|([a-zA-Z0-9-]+))?(?:\(([a-zA-Z0-9-.,\s]+)\))?'

gryml_mask = re.compile(r'^#(\[(.+)\])?{(.+)}' + pipe_mask, re.MULTILINE)
complex_value_mask = re.compile(r'([^{}]+)|\{([a-zA-Z0-9-_.]+)' + pipe_mask + r'\}')

logger = logging.Logger('gryml.core')


def get_comment(it, k, strip=True):
    comment = it.ca.items.get(k)
    if comment and comment[2]:
        value = comment[2].value
        match = gryml_mask.match(value)
        if match:
            if strip:
                it.ca.items.pop(k, None)
            return match.groups()[1:]


def apply_pipe(value, pipe, params):
    return Pipes.apply(pipe, value, *(params.split(',') if params else []))


def apply_comment(old_value, comment, strategy, values, pipe, params):

    def resolve(key, complex_pipe=None, complex_params=None):
        path = key.split('.')

        def report():
            print_warning(f'Warning, path `{key}` is not found in values, using `{old_value}` !')

        value = values
        for s in path:
            try:
                value = value.get(s)
            except Exception:
                report()
                return old_value
            finally:
                if value is None:
                    report()
                    return old_value

        if complex_pipe:
            value = apply_pipe(value, complex_pipe, complex_params)

        return value

    match = complex_value_mask.findall(comment)
    if match and len(match) > 1:
        res = [resolve(it[1], it[2], it[3]) if it[1] else it[0] for it in match]
        value = ''.join(res)
    else:
        value = resolve(comment)

    if pipe:
        value = apply_pipe(value, pipe, params)

    param = None

    # TODO: this mess needs to be sorted out asap
    if strategy is None:
        strategy = 'set'
    else:
        match = Strategies.strategy_mask.match(strategy)
        if match:
            strategy, _, param = Strategies.strategy_mask.match(strategy).groups()

    return Strategies.apply(strategy, old_value, value, param)


def process(rd, values, strip_comments=True):

    for k, v in rd.items():

        if isinstance(v, OrderedDict):
            process(rd[k], values, strip_comments)
        elif isinstance(v, list):
            for it in rd[k]:
                if isinstance(it, OrderedDict):
                    process(it, values, strip_comments)

        parsed = get_comment(rd, k, strip_comments)
        if parsed:
            strategy, comment, pipe, params = parsed
            if comment:
                rd[k] = apply_comment(v, comment, strategy, values, pipe, params)


def load(path):

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    if path.is_file():
        with open(path) as rd:
            yaml = YAML(typ=['safe', 'rt'])
            prd = yaml.load_all(rd)
            for it in prd:
                yield path, it

    elif path.is_dir():
        for sub_dir in path.iterdir():
            for sub_path, it in load(sub_dir):
                yield sub_path, it


def load_values(values_file, base_values):
    # TODO:
    logger.warning("loading values %s", values_file)

    sources = []
    yaml = YAML(typ=['safe', 'rt'])
    values = yaml.load(Path(values_file))

    if 'gryml' in values:
        for it in values['gryml']:
            if 'import' in it:
                parent_values, extra_sources = load_values(
                    Path(values_file).parent.resolve() / it['import'],
                    base_values
                )
                sources.extend(extra_sources)
                base_values.update(parent_values)
            elif 'source' in it:
                sources.append(Path(values_file).parent.resolve() / it['source'])

    process(values, base_values)
    base_values.update(values)
    return base_values, sources


def print_definition(it, pipe=sys.stdout):
    print('---', file=pipe)
    yaml = YAML()
    yaml.dump(it, pipe)


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


def deep_merge(values, new_values):
    # TODO: this is very simplistic, ignores lists
    #  also it might be worth it to use strategies here
    for k, v in new_values.items():
        if isinstance(v, dict):
            deep_merge(values[k], v)
        else:
            values[k] = v


def dispatch(parsed):
    values = {}
    sources = []

    if parsed.with_values:
        # TODO: negative cases and tests
        values.update(parse_values(parsed.with_values))

    if parsed.values_file:
        values, extra_sources = load_values(parsed.values_file, values)
        sources.extend(extra_sources)

    if parsed.set:
        # TODO: negative cases and tests
        deep_merge(values, parse_values(parsed.set))

    if parsed.path:
        sources.append(parsed.path)

    for source in sources:
        for path, it in load(source):
            process(it, values, not parsed.preserve_comments)
            print_definition(it)
            if parsed.echo:
                print('===', file=sys.stderr)
                print(path, file=sys.stderr)
                print_definition(it, sys.stderr)
