import base64
import hashlib
import random
import string

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


Pipes.pipe('lowercase', lambda v, core: str(v).lower())
Pipes.pipe('limit', lambda v, length, core: str(v)[:int(length)])


@Pipes.pipe('k8sName')
def k8s_name(v, core):
    max_len = 64
    if len(v) > max_len:
        print_warning("Trimmed k8s name: ", v, "to", max_len)
    return str(v)[:max_len]


@Pipes.pipe('b64enc')
def b64_enc(v, core):
    return base64.b64encode(str(v).encode()).decode()


@Pipes.pipe('randstr')
def randstr(v, core):
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(v))


@Pipes.pipe('source')
def source(v, core):
    with open(core.resolve(v)) as f:
        return f.read()


@Pipes.pipe('sha256')
def sha256(v, core):
    sha_sum = hashlib.sha256()
    sha_sum.update(v.encode())
    return base64.b64encode(sha_sum.digest()).decode()


@Pipes.pipe('valmap')
def valmap(val, pipe, core):
    return {k: Pipes.apply(pipe, v, core) for k, v in val.items()}
