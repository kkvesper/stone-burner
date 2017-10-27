
from __future__ import print_function

import copy
import os
import signal
import shutil
import sys

from config import DEFAULT_VARS_DIR
from config import OPTIONS_BY_COMMAND
from config import TFAttributes

from options import validate_components
from options import validate_environment
from options import validate_project

from utils import debug
from utils import error
from utils import exec_command
from utils import info
from utils import success


def run_command(cmd, project, component, component_config, environment, verbose=0, *args, **kwargs):
    exec_dir = os.getcwd()
    state_dir = os.path.abspath(os.path.join('./states', environment, project, component))
    config_dir = os.path.abspath(os.path.join('./projects', project, component_config.get('component', component)))

    config_files = os.listdir(config_dir)

    new_kwargs = copy.deepcopy(kwargs)
    new_kwargs['tf_args'] = []  # Don't want to send extra params to get and init commands

    need_init = (
        os.environ.get('TF_INIT', '0') == '1' or
        not os.path.exists(state_dir) or
        'terraform.tfstate' not in os.listdir(state_dir) or
        'plugins' not in os.listdir(state_dir)
    )

    os.chdir(config_dir)

    def save_state():
        if verbose > 2:
            debug('Saving state into states dir...')

        if os.path.exists(state_dir) and os.path.exists('.terraform'):
            shutil.rmtree(state_dir)

        if os.path.exists('.terraform'):
            shutil.move('.terraform', state_dir)

        # Move also other new possible generated files from the terraform command
        new_files = list(set(os.listdir(config_dir)) - set(config_files))

        for f in new_files:
            shutil.move(f, os.path.join(state_dir, f))

        os.chdir(exec_dir)

    def handle_init_error():
        error('There was an error executing your command. Please check the Terraform output.')
        save_state()
        sys.exit(1)

    def pre_cmd_msg():
        if verbose > 0:
            info('Running Terraform command: %s' % ' '.join(cmd))
            info('<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>')
            info('           COMMAND OUTPUT')
            info()

    def handle_cmd_success():
        if verbose > 0:
            success()
            success('OK!')

    def handle_cmd_error():
        error()
        error('There was an error executing your command. Please check the Terraform output.')
        sys.exit(1)

    def handle_cmd_end():
        if verbose > 0:
            info('<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>')

        save_state()

    if need_init:
        init_tf_cmd = 'init'

        def init_pre_func():
            info('State not found or init forced, Initializing with terraform init...') if verbose > 0 else None
    else:
        init_tf_cmd = 'get'

        def init_pre_func():
            info('Fetching modules with terraform get...') if verbose > 0 else None

    init_cmd = build_command(
        *args,
        command=init_tf_cmd,
        project=project,
        component=component,
        component_config=component_config,
        environment=environment,
        **new_kwargs
    )

    if os.path.exists(state_dir):
        shutil.move(state_dir, '.terraform')
        state_cached = True
    else:
        if not os.path.exists('.terraform'):
            os.makedirs('.terraform')

        state_cached = False

    def rollback_state(signal, frame):
        info('Ctrl+C pressed. Rolling back state...') if verbose > 0 else None

        if state_cached:
            shutil.move('.terraform', state_dir)
        else:
            shutil.rmtree('.terraform')

        os.chdir(exec_dir)
        sys.exit(0)

    signal.signal(signal.SIGINT, rollback_state)

    exec_command(
        cmd=init_cmd,
        pre_func=init_pre_func,
        except_func=handle_init_error,
    )

    exec_command(
        cmd=cmd,
        pre_func=pre_cmd_msg,
        except_func=handle_cmd_error,
        else_func=handle_cmd_success,
        finally_func=handle_cmd_end,
    )


def build_command(command, tf_args=[], options_by_command=OPTIONS_BY_COMMAND, *args, **kwargs):
    options = []
    arguments = []

    if ' ' in command:
        commands = command.split()
        command = commands[0]
        subcommands = commands[1:]
    else:
        subcommands = []

    for option in options_by_command.get(command, {}).get('options', []):
        func_name = option.replace('-', '_')
        func = getattr(TFAttributes, func_name)

        values = func(TFAttributes(), *args, **kwargs)
        options += ['-%s=%s' % (option, value) for value in values]

    for arg in options_by_command.get(command, {}).get('args', []):
        func_name = arg.replace('-', '_')
        func = getattr(TFAttributes, func_name)

        values = func(TFAttributes(), *args, **kwargs)
        arguments += values

    return ['terraform', command] + subcommands + options + list(tf_args) + arguments


def check_validation(project, component, environment, component_config, vars_dir=DEFAULT_VARS_DIR, verbose=0):
    title = '%s %s - %s %s' % ('=' * 10, project, component, '=' * 10)

    variables = component_config.get('variables', component)
    vars_file = os.path.join(vars_dir, environment, project, '%s.tfvars' % variables)

    if verbose > 0:
        info(title)

    # Don't validate projects without variables file
    if not os.path.exists(vars_file):
        if verbose > 0:
            info('Skipping validation. Reason: vars-file "%s" not found.' % vars_file)
            success('OK!')

        return False

    validate_config = component_config.get('validate', None)

    if validate_config and 'skip' in validate_config:
        if verbose > 0:
            info('Skipping validation. Reason: "skip" found in the configuration.')
            success('OK!')

        return False

    return True


def run(command, project, components, environment, config, exclude_components=[], verbose=0, *args, **kwargs):
    project = validate_project(project, config)

    # If no component is chosen, use all of them
    components = components if components else config['projects'][project].keys()
    components = list(set(components) - set(exclude_components))
    components = validate_components(components, project, config)

    environment = validate_environment(environment, config)

    for component in components:
        component_config = config['projects'][project][component] or {}

        if command == 'validate':
            should_validate = check_validation(
                project=project,
                component=component,
                environment=environment,
                component_config=component_config,
                verbose=verbose,
            )

            if not should_validate:
                continue

        cmd = build_command(
            *args,
            command=command,
            project=project,
            component=component,
            component_config=component_config,
            environment=environment,
            config=config,
            verbose=verbose,
            **kwargs
        )

        if verbose > 0:
            info('::::::::::::::::::::::::::::::::::::::::::::::')
            info('PROJECT =======> %s - %s' % (project, component))

        run_command(
            *args,
            cmd=cmd,
            project=project,
            component=component,
            component_config=component_config,
            environment=environment,
            config=config,
            verbose=verbose,
            **kwargs
        )

        if verbose > 0:
            info('::::::::::::::::::::::::::::::::::::::::::::::')
            info()
            info()
