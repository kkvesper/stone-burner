#!/usr/bin/env python

from __future__ import print_function

import click

from lib import run

from options import config_file_option
from options import components_option
from options import component_types_option
from options import environment_option
from options import exclude_components_option
from options import validate_project
from options import verbose_option


@click.group()
def main():
    """Give more power to Terraform."""
    pass


@config_file_option()
@main.command('projects')
def projects(config):
    """Display available projects in your configuration."""
    projects = config['projects'].keys()

    print('Available projects:')
    for project in projects:
        print('- %s' % project)


@config_file_option()
@component_types_option()
@click.argument('project', type=str)
@main.command('components')
def components(project, component_type, config):
    """Display available components for a project in your configuration."""
    validate_project(project, config)
    components = config['projects'][project].keys()

    if component_type:
        print('Available components for project "%s" of type(s) "%s":' % (project, ', '.join(component_type)))
    else:
        print('Available components for project "%s":' % project)

    for component in components:
        should_print = True

        if component_type:
            component_config = config['projects'][project][component] or {}
            ct = component_config.get('component', component)

            if ct not in component_type:
                should_print = False

        if should_print:
            print('- %s' % component)


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@environment_option()
@exclude_components_option()
@components_option()
@config_file_option()
@click.argument('project', type=str)
@main.command('plan', context_settings=dict(ignore_unknown_options=True))
def tf_plan(project, components, exclude_components, environment, config, verbose, tf_args):
    """Terraform plan command (https://www.terraform.io/docs/commands/plan.html)."""
    run(
        command='plan',
        project=project,
        components=components,
        exclude_components=exclude_components,
        environment=environment,
        config=config,
        tf_args=tf_args,
        verbose=verbose,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@components_option()
@click.argument('project', type=str)
@main.command('apply', context_settings=dict(ignore_unknown_options=True))
def tf_apply(project, components, exclude_components, environment, config, verbose, tf_args):
    """Terraform apply command (https://www.terraform.io/docs/commands/apply.html)."""
    run(
        command='apply',
        project=project,
        components=components,
        exclude_components=exclude_components,
        environment=environment,
        config=config,
        tf_args=tf_args,
        verbose=verbose,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@components_option()
@click.argument('project', type=str)
@main.command('destroy', context_settings=dict(ignore_unknown_options=True))
def tf_destroy(project, components, exclude_components, environment, config, verbose, tf_args):
    """Terraform destroy command (https://www.terraform.io/docs/commands/destroy.html)."""
    run(
        command='destroy',
        project=project,
        components=components,
        exclude_components=exclude_components,
        environment=environment,
        config=config,
        tf_args=tf_args,
        verbose=verbose,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@components_option()
@click.argument('project', type=str)
@main.command('refresh', context_settings=dict(ignore_unknown_options=True))
def tf_refresh(project, components, exclude_components, environment, config, verbose, tf_args):
    """Terraform refresh command (https://www.terraform.io/docs/commands/refresh.html)."""
    run(
        command='refresh',
        project=project,
        components=components,
        exclude_components=exclude_components,
        environment=environment,
        config=config,
        tf_args=tf_args,
        verbose=verbose,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@components_option()
@click.argument('project', type=str)
@main.command('validate', context_settings=dict(ignore_unknown_options=True))
def tf_validate(project, components, exclude_components, environment, config, verbose, tf_args):
    """Terraform validate command (https://www.terraform.io/docs/commands/validate.html)."""
    run(
        command='validate',
        project=project,
        components=components,
        exclude_components=exclude_components,
        environment=environment,
        config=config,
        tf_args=tf_args,
        verbose=verbose,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@click.argument('id', type=str)
@click.argument('address', type=str)
@click.argument('component', type=str)
@click.argument('project', type=str)
@main.command('import', context_settings=dict(ignore_unknown_options=True))
def tf_import(project, component, address, id, environment, config, verbose, tf_args):
    """Terraform import command (https://www.terraform.io/docs/import/index.html)."""
    run(
        command='import',
        project=project,
        components=[component],
        environment=environment,
        config=config,
        tf_args=tf_args,
        verbose=verbose,
        address=address,
        id=id,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@components_option()
@click.argument('project', type=str)
@click.argument('subcommand', type=click.Choice(['list', 'mv', 'pull', 'push', 'rm', 'show']))
@main.command('state', context_settings=dict(ignore_unknown_options=True))
def tf_state(subcommand, project, components, exclude_components, environment, config, verbose, tf_args):
    """Terraform state command (https://www.terraform.io/docs/commands/state/index.html)."""
    run(
        command='state %s' % subcommand,
        project=project,
        components=components,
        exclude_components=exclude_components,
        environment=environment,
        config=config,
        tf_args=tf_args,
        verbose=verbose,
    )


if __name__ == '__main__':
    main()
