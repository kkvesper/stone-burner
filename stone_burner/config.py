import os

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
        'options': ['var-file', 'state'],
        'args': [],
    },
    'apply': {
        'options': ['var-file', 'state'],
        'args': [],
    },
    'destroy': {
        'options': ['var-file', 'state'],
        'args': [],
    },
    'refresh': {
        'options': ['var-file', 'state'],
        'args': [],
    },
    'import': {
        'options': ['var-file', 'state'],
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
    def __init__(
        self,
        root_dir=DEFAULT_ROOT_DIR,
        projects_dir=DEFAULT_PROJECTS_DIR,
        states_dir=DEFAULT_STATES_DIR,
        vars_dir=DEFAULT_VARS_DIR
    ):
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

    def state(*args, **kwargs):
        return ['./.terraform/terraform.tfstate']
