from gryml.utils import print_warning


class Pipes:

    pipes = {}

    @classmethod
    def pipe(cls, name, handler=None):
        if handler:
            cls.pipes[name] = handler
        else:
            def decorator(func):
                cls.pipes[name] = func
            return decorator

    @classmethod
    def apply(cls, name, value, *args):
        return cls.pipes[name](value, *args)


Pipes.pipe('lowercase', lambda v: str(v).lower())
Pipes.pipe('limit', lambda v, length: str(v)[:int(length)])


@Pipes.pipe('k8s-name')
def k8s_name(v):
    max_len = 64
    if len(v) > max_len:
        print_warning("Trimmed k8s name: ", v, "to", max_len)
    return str(v)[:max_len]
