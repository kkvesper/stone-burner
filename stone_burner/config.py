import os
import six


DEFAULT_STONE_BURNER_DIR = os.path.join(os.path.expanduser("~"), '.stoneburner')
DEFAULT_ROOT_DIR = os.path.abspath(os.getcwd())
DEFAULT_STATES_DIR = os.path.abspath('./states')
DEFAULT_PROJECTS_DIR = os.path.abspath('./projects')
DEFAULT_VARS_DIR = os.path.abspath('./variables')

OPTIONS_BY_COMMAND = {
    'init': {
        'options': ['backend', 'backend-config', 'plugin-dir', 'get-plugins'],
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


def parse_project_config(config, project):
    result = {}
    p_config = config['projects'][project]

    for elem in p_config:
        if isinstance(elem, six.string_types):
            result[elem] = {
                'component_type': elem,
                'validate': {},
            }
        elif isinstance(elem, dict):
            d_keys = list(elem.keys())

            if len(d_keys) != 1:
                raise Exception(
                    'Bad config for project: components defined as dictionaries must have exactly 1 key')

            component_type = d_keys[0]  # The only key is the component type
            info = elem[component_type]

            if isinstance(info, list):
                # It's a list of components from the same type
                for c in info:
                    if isinstance(c, six.string_types):
                        result[c] = {
                            'component_type': component_type,
                            'validate': {},
                        }
                    elif isinstance(c, dict):
                        d_keys = list(c.keys())

                        if len(d_keys) != 1:
                            raise Exception(
                                'Bad config for project: components defined as dictionaries must have exactly 1 key')

                        # The only key is the component type
                        component_name = d_keys[0]
                        c_info = c[component_name]

                        result[component_name] = {
                            'component_type': component_type,
                            'validate': c_info['validate'],
                        }
            elif isinstance(info, dict):
                # It's a component named the same as the component type with extra info
                result[component_type] = {
                    'component_type': component_type,
                    'validate': info['validate'],
                }

    return result


def get_plugins_dir():
    stone_burner_dir = os.environ.get(
        'STONE_BURNER_DIR', DEFAULT_STONE_BURNER_DIR
    )

    plugin_dir = os.path.join(stone_burner_dir, 'plugins')

    if not os.path.exists(stone_burner_dir):
        os.makedirs(stone_burner_dir)

    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)

    return plugin_dir


def get_component_paths(project, component, component_config, environment, states_dir=DEFAULT_STATES_DIR, projects_dir=DEFAULT_PROJECTS_DIR, vars_dir=DEFAULT_VARS_DIR):
    return {
        'state_dir': os.path.abspath(os.path.join(states_dir, environment, project, component)),
        'config_dir': os.path.abspath(os.path.join(projects_dir, project, component_config['component_type'])),
        'vars_file': os.path.abspath(os.path.join(vars_dir, environment, project, '%s.tfvars' % component)),
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
        self._plugin_dir = get_plugins_dir()

    @staticmethod
    def backend(*args, **kwargs):
        #pylint: disable=unused-argument
        no_remote = os.environ.get('STONE_BURNER_NO_REMOTE', '0')
        return ['false'] if no_remote == '1' else ['true']

    @staticmethod
    def backend_config(*args, **kwargs):
        #pylint: disable=unused-argument
        if os.environ.get('STONE_BURNER_NO_REMOTE', '0') == '1':
            return []

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

    def plugin_dir(self, *args, **kwargs):
        return [self._plugin_dir]

    @staticmethod
    def get_plugins(*args, **kwargs):
        return ['false']

    def var_file(self, *args, **kwargs):
        #pylint: disable=unused-argument
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

    @staticmethod
    def address(*args, **kwargs):
        #pylint: disable=unused-argument
        return [kwargs['address']]

    @staticmethod
    def id(*args, **kwargs):
        #pylint: disable=unused-argument
        return [kwargs['id']]

    @staticmethod
    def check_variables(*args, **kwargs):
        component_config = kwargs['component_config']
        validate_config = component_config.get('validate', {}) or {}
        check_variables = validate_config.get('check-variables', True)

        return ['true'] if check_variables else ['false']

    def state(self, *args, **kwargs):
        #pylint: disable=unused-argument
        project = kwargs['project']
        component = kwargs['component']
        environment = kwargs['environment']

        state_file = os.path.join(
            self.states_dir, environment, project, component, 'terraform.tfstate'
        )

        return [state_file]
