import logging

from jinja2 import Undefined

logger = logging.Logger('gryml.core')


def print_warning(*args):
    for it in args:
        logger.warning(f'\u001b[31m{str(it)}\u001b[0m')


class SilentUndefined(Undefined):

    def __getattr__(self, item):
        return self