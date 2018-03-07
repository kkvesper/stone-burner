import os
import click
import yaml


def config_file_option():
    class Config(click.ParamType):
        name = 'config'

        def convert(self, value, param, ctx):
            if not os.path.exists(value):
                self.fail('%s does not exist' % value)

            with open(value) as f:
                config = yaml.load(f)

            ctx.params['config'] = config
            return config

    return click.option(
        '-config',
        '--config-file',
        'config',
        type=Config(),
        default='config.yml',
        help='Configuration file to use.',
        show_default=True,
    )


def environment_option():
    return click.option(
        '-e',
        '--environment',
        type=str,
        help='Target environment (AWS account to use). '
             'Remember that your environment must be defined in your config.yml file.',
    )


def components_option():
    return click.option(
        '-c',
        '--components',
        type=str,
        default=[],
        help='Individual components to manage.',
        multiple=True,
    )


def exclude_components_option():
    return click.option(
        '-xc',
        '--exclude-components',
        type=str,
        default=[],
        help='Individual components to exclude.',
        multiple=True,
    )


def component_types_option():
    return click.option(
        '-ct',
        '--component-types',
        type=str,
        default=[],
        help='Apply your action only to the components which belong to this type.',
        multiple=True,
    )


def verbose_option():
    return click.option('-v', '--verbose', count=True)


def validate_project(project, config):
    valid_projects = config['projects'].keys()

    if project not in valid_projects:
        err_msg = 'invalid choice: %s. (choose from %s)' % (
            project,
            ', '.join(valid_projects),
        )

        raise click.BadParameter(err_msg, param_hint='"project"')

    return project


def validate_components(components, p_config):
    valid_components = p_config.keys()

    # Avoid duplicates
    components = list(set(components))

    for component in components:
        if component not in valid_components:
            err_msg = 'invalid choice: %s. (choose from %s)' % (
                component,
                ', '.join(valid_components),
            )

            raise click.BadParameter(err_msg, param_hint='"components"')

    return components


def validate_environment(environment, config):
    env_config = config['environments']

    if not environment:
        environment = [env['name'] for env in env_config if env.get('default', False)][0]

    valid_envs = [env['name'] for env in env_config]

    if environment not in valid_envs:
        err_msg = 'invalid choice: %s. (choose from %s)' % (
            environment,
            ', '.join(valid_envs),
        )

        raise click.BadParameter(err_msg, param_hint='"environment"')

    return environment
