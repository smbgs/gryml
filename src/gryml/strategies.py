from copy import deepcopy, copy

from jinja2 import Undefined
from ruamel.yaml import scalarstring

from gryml.utils import LazyString


class Strategies:

    strategies = {}

    @classmethod
    def strategy(cls, name, handler=None):
        if handler:
            cls.strategies[name] = handler
        else:
            def decorator(func):
                cls.strategies[name] = func
                return func
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

    if not context.get('value_used'):
        return None

    if not context.get('may_repeat'):
        return None

    if not context.get('is_list_item'):
        return old_value

    iterable = core.eval(value_expression, context)
    context['value_repeated'] = True
    context['value_used'] = False

    i_key = 'i'
    it_key = 'it'

    if strat_expression:
        i_key, it_key = str(strat_expression).strip().split(":")

    if isinstance(iterable, list):
        enumerated = enumerate(iterable)
    else:
        enumerated = iterable.items()

    for i, it in enumerated:

        values = {
            **context['values'],
            i_key: i,
            it_key: it
        }

        rules = context['rules'][1:]

        if rules and rules[0]['strat'] == 'repeat':
            rule = rules[0]
            repeat_value(core, old_value, rule['arg_exp'], rule['exp'], {
                **context,
                'tags': context['tags'],
                'path': context['path'],
                'rules': rules,
                'values': values,
                'value_used': True
            })
        else:
            updated = copy(core.process(deepcopy(old_value), context={
                'tags': context['tags'],
                'path': context['path'],
                'values': values
            }))
            # TODO: we might wanna rethink how this is implemented and return the mutator in the context

            if isinstance(updated, str):
                updated = LazyString(updated)

            core.store_context_values(updated, values)
            context['list'].append(updated)

    return None


@Strategies.strategy('set')
def set_value(core, old_value, strat_expression, value_expression, context):

    if not context.get('value_used'):
        return None

    value = core.eval(value_expression, context)
    if not isinstance(value, Undefined):
        return deepcopy(value)
    else:
        return old_value


@Strategies.strategy('append')
def append_value(core, old_value, strat_expression, value_expression, context):

    if not context.get('value_used'):
        return None

    value = core.eval(value_expression, context)
    if not isinstance(value, Undefined):
        return old_value + deepcopy(value)
    else:
        return old_value


@Strategies.strategy('merge')
def merge_value(core, old_value, strat_expression, value_expression, context):

    if not context.get('value_used'):
        return None

    # TODO: make pure?
    value = core.eval(value_expression, context)
    if not isinstance(value, Undefined):
        old_value.update(core.eval(value_expression, context))
    return old_value


@Strategies.strategy('merge-using')
def merge_using_value(core, old_value, strat_expression, value_expression, context):

    if not context.get('value_used'):
        return None

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


@Strategies.strategy('template')
def template(core, old_value, strat_expression, value_expression, context):

    if not context.get('value_used'):
        return None

    value = core.eval(value_expression, context)

    if strat_expression is None:
        strat_expression = 'jinja'

    if strat_expression == 'jinja':
        return scalarstring.preserve_literal(core.template(old_value, context))

    return old_value
