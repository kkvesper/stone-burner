import crayons


def add_signature(func):
    def wrapper(msg=''):
        if not msg:
            return func(msg)
        else:
            return func('[*] %s' % msg)

    return wrapper


@add_signature
def success(msg):
    print(crayons.green(msg, bold=True))


@add_signature
def info(msg):
    print(crayons.white(msg, bold=True))


@add_signature
def error(msg):
    print(crayons.red(msg, bold=True))


@add_signature
def debug(msg):
    print(crayons.blue(msg, bold=False))
