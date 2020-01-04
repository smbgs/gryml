from copy import copy, deepcopy

from jinja2 import Undefined


class Strategies:

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
    def apply(cls, name, core, old_value, strat_expression, value_expression, context):
        if name not in cls.strategies:
            raise NotImplementedError(f"Strategy {name} is not supported!")
        return cls.strategies[name](core, old_value, strat_expression, value_expression, context)


@Strategies.strategy('if')
def if_value(core, old_value, strat_expression, value_expression, context):

    condition = strat_expression if strat_expression else value_expression

    if core.eval(condition, context):
        context['may_repeat'] = True
        return core.eval(value_expression, context) or old_value

    context['may_repeat'] = False
    context['value_used'] = False
    return None


@Strategies.strategy('else')
def else_value(core, old_value, strat_expression, value_expression, context):
    if not context.get('value_used'):
        context['value_used'] = True
        return core.eval(value_expression, context)
    return old_value

@Strategies.strategy('repeat')
def repeat_value(core, old_value, strat_expression, value_expression, context):

    if not context.get('may_repeat'):
        return None

    if not context.get('is_list_item'):
        return old_value

    iterable = core.eval(value_expression, context)
    context['value_repeated'] = True
    context['value_used'] = False

    # TODO: this is not pure
    result = context['list']  # type: list

    for i, it in enumerate(iterable):
        # TODO: custom context values names
        updated = core.process(deepcopy(old_value), context=dict(
            offset=context['offset'],
            tags=context['tags'],
            values=dict(
                i=i,
                it=it
            )))
        result.append(updated)

    return None


@Strategies.strategy('set')
def set_value(core, old_value, strat_expression, value_expression, context):
    value = core.eval(value_expression, context)
    if not isinstance(value, Undefined):
        return deepcopy(value)
    else:
        return old_value


@Strategies.strategy('append')
def append_value(core, old_value, strat_expression, value_expression, context):
    value = core.eval(value_expression, context)
    if not isinstance(value, Undefined):
        return old_value + deepcopy(value)
    else:
        return old_value


@Strategies.strategy('merge')
def merge_value(core, old_value, strat_expression, value_expression, context):
    # TODO: make pure?
    value = core.eval(value_expression, context)
    if not isinstance(value, Undefined):
        old_value.update(core.eval(value_expression, context))
    return old_value


@Strategies.strategy('merge-using')
def merge_using_value(core, old_value, strat_expression, value_expression, context):
    keys = set()
    value = core.eval(value_expression, context)

    for i, old_vi in enumerate(old_value):
        keys.add(old_vi[strat_expression])
        found_new_vi = next((new_vi for new_vi in value if new_vi[strat_expression] == old_vi[strat_expression]), None)
        if found_new_vi:
            old_value[i] = found_new_vi

    for new_vi in value:
        if new_vi[strat_expression] not in keys:
            old_value.append(new_vi)

    return old_value

