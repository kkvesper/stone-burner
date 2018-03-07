import os
import subprocess
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


def exec_command(
        cmd,
        tf_data_dir=None,
        pre_func=lambda: None,
        except_func=lambda: None,
        else_func=lambda: None,
        finally_func=lambda: None,
):
    pre_func()

    if tf_data_dir:
        os.environ['TF_DATA_DIR'] = tf_data_dir

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        except_func()
    else:
        else_func()
    finally:
        os.environ.pop('TF_DATA_DIR', None)
        finally_func()
