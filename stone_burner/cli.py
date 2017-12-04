#!/usr/bin/env python

from __future__ import print_function

import click
import os
import tempfile
import shutil
import subprocess

from config import get_plugins_dir

from lib import run

from options import validate_components
from options import config_file_option
from options import components_option
from options import component_types_option
from options import environment_option
from options import exclude_components_option
from options import validate_project
from options import verbose_option

from utils import exec_command


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


@verbose_option()
@exclude_components_option()
@components_option()
@config_file_option()
@click.argument('project', type=str)
@main.command('install')
def install(project, components, exclude_components, config, verbose):
    """Discover and downloads plugins from your components."""
    project = validate_project(project, config)

    # If no component is chosen, use all of them
    components = components if components else config['projects'][project].keys()

    components = list(set(components) - set(exclude_components))
    components = validate_components(components, project, config)

    plugin_dir = get_plugins_dir()

    for plugin in os.listdir(plugin_dir):
        if plugin.startswith('terraform-provider-terraform'):
            # Remove previous terraform plugin
            os.remove(os.path.join(plugin_dir, plugin))

    tf_bin = subprocess.check_output(['which', 'terraform']).split('\n')[0]
    tf_version = subprocess.check_output(['terraform', '-v']).split('\n')[0].split(' ')[1]
    tf_plugin_name = 'terraform-provider-terraform_%s_x4' % tf_version
    tf_plugin_path = os.path.join(plugin_dir, tf_plugin_name)
    shutil.copy2(tf_bin, tf_plugin_path)

    workdir = os.getcwd()

    for component in components:
        component_config = config['projects'][project][component] or {}

        config_dir = os.path.abspath(os.path.join(
            './projects', project, component_config.get('component', component)
        ))

        os.chdir(config_dir)

        temp_dir = tempfile.mkdtemp()

        exec_command(
            cmd=['terraform', 'init', '-backend=false', '-get=true', '-get-plugins=true', '-input=false'],
            tf_data_dir=temp_dir,
        )

        for root, dirs, filenames in os.walk(os.path.join(temp_dir, 'plugins')):
            for f in filenames:
                f_path = os.path.join(root, f)

                if f != 'lock.json':
                    # TODO: keep json.lock file and merge new ones
                    shutil.move(f_path, os.path.join(plugin_dir, f))

        shutil.rmtree(temp_dir)
        os.chdir(workdir)


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
