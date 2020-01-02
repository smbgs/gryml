import re


class Strategies:

    strategy_mask = re.compile(r'^([a-z-]+)(\s([a-zA-Z-]+))?$')
    strategies = {}

    @classmethod
    def strategy(cls, name, handler=None):
        if handler:
            cls.strategies[name] = handler
        else:
            def decorator(func):
                cls.strategies[name] = func
            return decorator

    @classmethod
    def apply(cls, name, old_value, value, param):
        if name not in cls.strategies:
            raise NotImplementedError(f"Strategy {name} is not supported!")
        return cls.strategies[name](old_value, value, param)


@Strategies.strategy('set')
def set_value(old_value, value, param):
    return value


@Strategies.strategy('append')
def append_value(old_value, value, param):
    return old_value + value


@Strategies.strategy('merge')
def merge_value(old_value, value, param):
    # TODO: make pure?
    old_value.update(value)
    return old_value


@Strategies.strategy('merge-using')
def merge_using_value(old_value, value, param):
    keys = set()
    for i, old_vi in enumerate(old_value):
        keys.add(old_vi[param])
        found_new_vi = next((new_vi for new_vi in value if new_vi[param] == old_vi[param]), None)
        if found_new_vi:
            old_value[i] = found_new_vi

    for new_vi in value:
        if new_vi[param] not in keys:
            old_value.append(new_vi)

    return old_value

