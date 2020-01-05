#!/usr/bin/python3

import argparse

import sys
from ruamel.yaml import YAML

from gryml.core import Gryml


def print_definition(it, pipe=sys.stdout):
    print('---', file=pipe)
    yaml = YAML()
    yaml.dump(it, pipe)


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

    gryml = Gryml(sys.stdout)

    if parsed.with_values:
        # TODO: negative cases and tests
        values.update(gryml.parse_values(parsed.with_values))

    if parsed.values_file:
        for source in sources:
            gryml.load_values(source, values, True, True, True, True)

    if parsed.set:
        # TODO: negative cases and tests
        deep_merge(gryml.values, gryml.parse_values(parsed.set))

    if parsed.path:
        gryml.sources.append(parsed.path)

    for path, result in gryml.process_sources():
        if parsed.echo:
            print('===', file=sys.stderr)
            print(path, file=sys.stderr)
            print_definition(result, sys.stderr)


def init_parser():
    arg_parser = argparse.ArgumentParser(description='Gryml yaml file processor')

    arg_parser.add_argument('path', nargs='?', default=None,
                            help='Path to the yam file or the directory with the yaml files')

    arg_parser.add_argument(
        '-f', dest='values_file', help='Primary values file that will be used to generate the resulting yaml'
    )

    arg_parser.add_argument(
        '--with', dest='with_values', action='append', help='Additional values that will be used as the base values'
    )

    arg_parser.add_argument(
        '--set', action='append', help='Additional values that will override the final values'
    )

    # TODO: this flag is not supported in gryml yet
    # arg_parser.add_argument(
    #     '--preserve-comments', default=False, action='store_true',
    #     help='Flag that controls if the yaml comments should be preserved in the output'
    # )

    arg_parser.add_argument(
        '--echo', default=False, action='store_true',
        help='Flag that controls if the output should also be echoed into the stdout'
    )

    return arg_parser


def main():
    parser = init_parser()
    dispatch(parser.parse_args(sys.argv[1:]))


if __name__ == '__main__':
    main()
