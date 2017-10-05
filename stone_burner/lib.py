
from __future__ import print_function

import os
import copy
import shutil
import subprocess
import sys

from options import validate_components
from options import validate_environment
from options import validate_project

from utils import debug
from utils import error
from utils import info
from utils import success


DEFAULT_ROOT_DIR = os.path.abspath(os.getcwd())
DEFAULT_STATES_DIR = os.path.abspath('./states')
DEFAULT_PROJECTS_DIR = os.path.abspath('./projects')
DEFAULT_VARS_DIR = os.path.abspath('./variables')


OPTIONS_BY_COMMAND = {
    'init': {
        'options': ['backend', 'backend-config'],
        'args': []
    },
    'get': {
        'options': [],
        'args': []
    },
    'plan': {
        'options': ['var-file'],
        'args': [],
    },
    'apply': {
        'options': ['var-file'],
        'args': [],
    },
    'destroy': {
        'options': ['var-file'],
        'args': [],
    },
    'refresh': {
        'options': ['var-file'],
        'args': [],
    },
    'import': {
        'options': ['var-file'],
        'args': ['address', 'id'],
    },
    'validate': {
        'options': ['var-file', 'check-variables'],
        'args': [],
    },
    'state': {
        'options': [],
        'args': [],
    },
}


class TFAttributes(object):
    def __init__(self, root_dir=DEFAULT_ROOT_DIR, projects_dir=DEFAULT_PROJECTS_DIR, states_dir=DEFAULT_STATES_DIR, vars_dir=DEFAULT_VARS_DIR):
        self.root_dir = root_dir
        self.projects_dir = projects_dir
        self.states_dir = states_dir
        self.vars_dir = vars_dir

    def backend(*args, **kwargs):
        no_remote = os.environ.get('TF_NO_REMOTE', '0')
        return ['false'] if no_remote == '1' else ['true']

    def backend_config(*args, **kwargs):
        project = kwargs['project']
        component = kwargs['component']
        environment = kwargs['environment']
        config = kwargs['config']

        state_key = os.path.join(environment, project, '%s.tfstate' % component)

        env_config = {
            env['name']: [
                'bucket=%s' % env['states_bucket'],
                'profile=%s' % env['aws_profile'],
                'key=%s' % state_key,
            ]
            for env in config['environments']
        }

        return env_config[environment]

    def var_file(self, *args, **kwargs):
        project = kwargs['project']
        component = kwargs['component']
        environment = kwargs['environment']
        component_config = kwargs['component_config']

        result = []

        shared_vars_file = os.path.join(self.vars_dir, environment, project, 'shared.tfvars')
        variables = component_config.get('variables', component)
        vars_file = os.path.join(self.vars_dir, environment, project, '%s.tfvars' % variables)

        if os.path.exists(shared_vars_file):
            result.append(shared_vars_file)

        if os.path.exists(vars_file):
            result.append(vars_file)

        return result

    def address(*args, **kwargs):
        return [kwargs['address']]

    def id(*args, **kwargs):
        return [kwargs['id']]

    def check_variables(*args, **kwargs):
        component_config = kwargs['component_config']
        validate_config = component_config.get('validate', {})
        check_variables = validate_config.get('check-variables', True)

        return ['true'] if check_variables else ['false']


def exec_command(cmd, pre_func=lambda: None, except_func=lambda: None, else_func=lambda: None, finally_func=lambda: None):
    pre_func()

    try:
        subprocess.check_call(cmd)
    except Exception:
        except_func()
    else:
        else_func()
    finally:
        finally_func()


def run_command(cmd, project, component, component_config, environment, verbose=0, *args, **kwargs):
    exec_dir = os.getcwd()
    state_dir = os.path.abspath(os.path.join('./states', environment, project, component))
    config_dir = os.path.abspath(os.path.join('./projects', project, component_config.get('component', component)))

    new_kwargs = copy.deepcopy(kwargs)
    new_kwargs['tf_args'] = []  # Don't want to send extra params to get and init commands

    need_init = (
        os.environ.get('TF_INIT', '0') == '1' or
        not os.path.exists(state_dir) or
        'terraform.tfstate' not in os.listdir(state_dir)
    )

    os.chdir(config_dir)

    def save_state():
        if verbose > 2:
            debug('Saving state into states dir...')

        if need_init and os.path.exists(state_dir):
            shutil.rmtree(state_dir)

        if os.path.exists('.terraform'):
            shutil.move('.terraform', state_dir)

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
        # Set the remote config
        init_cmd = build_command(
            *args,
            command='init',
            project=project,
            component=component,
            component_config=component_config,
            environment=environment,
            **new_kwargs
        )

        exec_command(
            cmd=init_cmd,
            pre_func=lambda: info('State not found or init forced, Initializing with terraform init...') if verbose > 0 else None,
            except_func=handle_init_error,
        )
    else:
        shutil.move(state_dir, '.terraform')

        get_cmd = build_command(
            *args,
            command='get',
            project=project,
            component=component,
            component_config=component_config,
            environment=environment,
            **new_kwargs
        )

        exec_command(
            cmd=get_cmd,
            pre_func=lambda: info('State found, fetching modules with terraform get...') if verbose > 0 else None,
            except_func=handle_init_error,
        )

    exec_command(
        cmd=cmd,
        pre_func=pre_cmd_msg,
        except_func=handle_cmd_error,
        else_func=handle_cmd_success,
        finally_func=handle_cmd_end,
    )


def build_command(command, tf_args=[], *args, **kwargs):
    options = []
    arguments = []

    if ' ' in command:
        commands = command.split()
        command = commands[0]
        subcommands = commands[1:]
    else:
        subcommands = []

    for option in OPTIONS_BY_COMMAND.get(command, {}).get('options', []):
        func_name = option.replace('-', '_')
        func = getattr(TFAttributes, func_name)

        values = func(TFAttributes(), *args, **kwargs)
        options += ['-%s=%s' % (option, value) for value in values]

    for arg in OPTIONS_BY_COMMAND.get(command, {}).get('args', []):
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
