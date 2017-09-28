
from __future__ import print_function

import os
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


OPTIONS_BY_COMMAND = {
    'init': {
        'options': ['backend', 'backend-config'],
        'args': ['config']
    },
    'get': {
        'options': [],
        'args': ['config']
    },
    'plan': {
        'options': ['var-file', 'state'],
        'args': ['config'],
    },
    'apply': {
        'options': ['var-file', 'state'],
        'args': ['config'],
    },
    'destroy': {
        'options': ['var-file', 'state'],
        'args': ['config'],
    },
    'refresh': {
        'options': ['var-file', 'state'],
        'args': ['config'],
    },
    'import': {
        'options': ['var-file', 'state', 'config'],
        'args': ['address', 'id'],
    },
    'validate': {
        'options': ['var-file', 'check-variables'],
        'args': ['config'],
    },
}


class TFAttributes(object):
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

    def var_file(*args, **kwargs):
        project = kwargs['project']
        component = kwargs['component']
        environment = kwargs['environment']
        component_config = kwargs['component_config']

        result = []

        vars_dir = os.path.abspath('./variables')
        shared_vars_file = os.path.join(vars_dir, environment, project, 'shared.tfvars')
        variables = component_config.get('variables', component)
        vars_file = os.path.join(vars_dir, environment, project, '%s.tfvars' % variables)

        if os.path.exists(shared_vars_file):
            result.append(shared_vars_file)

        if os.path.exists(vars_file):
            result.append(vars_file)

        return result

    def state(*args, **kwargs):
        return ['./.terraform/terraform.tfstate']

    def config(*args, **kwargs):
        project = kwargs['project']
        component = kwargs['component']
        component_config = kwargs['component_config']

        projects_dir = os.path.abspath('./projects')
        component_dir = component_config.get('component', component)
        project_dir = os.path.join(projects_dir, project, component_dir)

        return [project_dir]

    def address(*args, **kwargs):
        return [kwargs['address']]

    def id(*args, **kwargs):
        return [kwargs['id']]

    def check_variables(*args, **kwargs):
        component_config = kwargs['component_config']
        validate_config = component_config.get('validate', {})
        check_variables = validate_config.get('check-variables', True)

        return ['true'] if check_variables else ['false']


def run_command(cmd, project, component, environment, verbose=0, *args, **kwargs):
    state_dir = os.path.join('./states', environment, project, component)

    # Creating the environment folder
    if not os.path.exists(state_dir):
        if verbose > 2:
            debug('State dir "%s" does not exist. Initializing folder...' % state_dir)

        os.makedirs(state_dir)

    # Cleaning current terraform cache folder
    if os.path.exists('.terraform'):
        if verbose > 2:
            debug('Removing cache folder: "%s"...' % os.path.join(os.getcwd(), '.terraform'))

        shutil.rmtree('.terraform')

    if verbose > 2:
        debug(
            'Caching state: moving state folder "%s" to "%s"...' % (
                state_dir, os.path.join(os.getcwd(), '.terraform'))
        )

    # Retrieve the preview cached state
    shutil.move(state_dir, '.terraform')

    if os.environ.get('TF_INIT', '0') == '1':
        # Set the remote config
        init_cmd = build_command(
            *args,
            command='init',
            project=project,
            component=component,
            environment=environment,
            **kwargs
        )

        if verbose > 0:
            info('Initializing project...')
            info()
            info(' '.join(init_cmd))

        subprocess.check_call(init_cmd)
    else:
        # Fetch modules
        get_cmd = build_command(
            *args,
            command='get',
            project=project,
            component=component,
            environment=environment,
            **kwargs
        )

        if verbose > 0:
            info('Fetching modules.')
            info(' '.join(get_cmd))

        subprocess.check_call(get_cmd)

    if verbose > 0:
        info('Running Terraform command:')
        info(' '.join(cmd))

    try:
        subprocess.check_call(cmd)
    except Exception:
        if verbose > 2:
            raise
        else:
            error('There was an error. Please check the Terraform output or increase verbosity')
            sys.exit(1)
    else:
        if verbose > 0:
            success('OK!')
    finally:
        # Save the cached state
        if verbose > 2:
            debug(
                'Saving cached state: moving state folder "%s" to "%s"...' % (
                    os.path.join(os.getcwd(), '.terraform'), state_dir)
            )

        shutil.move('.terraform', state_dir)


def build_command(command, tf_args=[], *args, **kwargs):
    options = []
    arguments = []

    for option in OPTIONS_BY_COMMAND[command]['options']:
        func_name = option.replace('-', '_')
        func = getattr(TFAttributes, func_name)

        values = func(TFAttributes(), *args, **kwargs)
        options += ['-%s=%s' % (option, value) for value in values]

    for arg in OPTIONS_BY_COMMAND[command]['args']:
        func_name = arg.replace('-', '_')
        func = getattr(TFAttributes, func_name)

        values = func(TFAttributes(), *args, **kwargs)
        arguments += values

    return ['terraform', command] + options + list(tf_args) + arguments


def check_validation(project, component, environment, component_config, verbose=0):
    title = '%s %s - %s %s' % ('=' * 10, project, component, '=' * 10)

    variables = component_config.get('variables', component)
    vars_file = os.path.join('./variables', environment, project, '%s.tfvars' % variables)

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
                project,
                component,
                environment,
                component_config,
                verbose,
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
