commands = dict()


def command(fn):
    commands[fn.__name__] = fn
    return fn
