#!/usr/bin/python3

import argparse

import sys

from gryml.core import dispatch


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

    arg_parser.add_argument(
        '--preserve-comments', default=False, action='store_true',
        help='Flag that controls if the yaml comments should be preserved in the output'
    )

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
