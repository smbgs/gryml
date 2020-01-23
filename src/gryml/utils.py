import logging

from jinja2 import Undefined

logger = logging.Logger('gryml.core')


def print_warning(*args):
    for it in args:
        logger.warning(f'\u001b[31m{str(it)}\u001b[0m')


def deep_merge(values, new_values):
    # TODO: this is very simplistic, ignores lists
    #  also it might be worth it to use strategies here
    for k, v in new_values.items():
        if isinstance(v, dict):
            if k not in values:
                values[k] = dict()
            deep_merge(values[k], v)
        else:
            values[k] = v


class SilentUndefined(Undefined):

    def __getattr__(self, item):
        return self


class LazyString(str):
    pass
