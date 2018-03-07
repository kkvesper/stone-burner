import copy
import os
import sys

from .config import OPTIONS_BY_COMMAND
from .config import TFAttributes
from .config import parse_project_config
from .config import get_component_paths

from .options import validate_components
from .options import validate_environment
from .options import validate_project

from .utils import error
from .utils import exec_command
from .utils import info
from .utils import success


def run_command(cmd, project, component, component_config, environment, verbose=0, *args, **kwargs):
    work_dir = os.getcwd()
    c_paths = get_component_paths(project, component, component_config, environment)
    state_dir = c_paths['state_dir']
    config_dir = c_paths['config_dir']

    new_kwargs = copy.deepcopy(kwargs)
    new_kwargs['tf_args'] = []  # Don't want to send extra params to get and init commands

    need_init = (
        os.environ.get('TF_INIT', '0') == '1' or
        not os.path.exists(state_dir) or
        'terraform.tfstate' not in os.listdir(state_dir) or
        'plugins' not in os.listdir(state_dir) or
        'plugin_path' not in os.listdir(state_dir)
    )

    os.chdir(config_dir)

    def handle_init_error():
        error('There was an error executing your command. Please check the Terraform output.')
        sys.exit(1)

    def pre_cmd_msg():
        if verbose >= 0:
            info('Running Terraform command: %s' % ' '.join(cmd))
            info('<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>')
            info('           COMMAND OUTPUT')
            info('')

    def handle_cmd_success():
        if verbose >= 0:
            success('OK!')

    def handle_cmd_error():
        error('')
        error('There was an error executing your command. Please check the Terraform output.')
        sys.exit(1)

    def handle_cmd_end():
        if verbose >= 0:
            info('<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>')

    init_tf_cmd = 'init' if need_init else 'get'

    init_cmd = build_command(
        *args,
        command=init_tf_cmd,
        project=project,
        component=component,
        component_config=component_config,
        environment=environment,
        **new_kwargs
    )

    def init_pre_func():
        if need_init:
            info('State not found or init forced, Initializing with terraform init...')
        else:
            info('Fetching modules with terraform get...')

        if verbose > 0:
            info('Running init command: %s' % ' '.join(init_cmd))

    exec_command(
        cmd=init_cmd,
        tf_data_dir=state_dir,
        pre_func=init_pre_func,
        except_func=handle_init_error,
        else_func=handle_cmd_success,
    )

    exec_command(
        cmd=cmd,
        tf_data_dir=state_dir,
        pre_func=pre_cmd_msg,
        except_func=handle_cmd_error,
        else_func=handle_cmd_success,
        finally_func=handle_cmd_end,
    )

    os.chdir(work_dir)


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


def check_validation(project, component, environment, component_config, verbose=0):
    title = '%s %s - %s %s' % ('=' * 10, project, component, '=' * 10)
    c_paths = get_component_paths(project, component, component_config, environment)

    vars_file = c_paths['vars_file']

    if verbose >= 0:
        info(title)

    # Don't validate projects without variables file
    if not os.path.exists(vars_file):
        if verbose >= 0:
            info('Skipping validation. Reason: vars file "%s" not found.' % vars_file)
            success('OK!')

        return False

    validate_config = component_config.get('validate', None)

    if validate_config and 'skip' in validate_config:
        if verbose >= 0:
            info('Skipping validation. Reason: "skip" found in the configuration.')
            success('OK!')

        return False

    return True


def run(command, project, components, environment, config, component_types=[], exclude_components=[], verbose=0, *args, **kwargs):
    project = validate_project(project, config)
    p_components = parse_project_config(config, project)

    if component_types:
        p_components = {
            c: p_components[c]
            for c in p_components.keys()
            if p_components[c]['component_type'] in component_types
        }

        if not p_components:
            raise Exception("There isn't any component belonging to the specified types")

    if components:
        components = validate_components(components, p_components)
    else:
        # If no component is chosen, use all of them
        components = list(p_components.keys())

    components = list(set(components) - set(exclude_components))
    environment = validate_environment(environment, config)

    for component in components:
        component_config = p_components[component] or {}

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

        if verbose >= 0:
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

        if verbose >= 0:
            info('::::::::::::::::::::::::::::::::::::::::::::::')
            info('')
            info('')
