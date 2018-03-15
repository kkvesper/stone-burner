#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import click

from stone_burner import __version__

from .config import get_plugins_dir
from .config import parse_project_config

from .install import install_terraform_plugin
from .install import manual_install
from .install import discover_and_install

from .lib import run

from .options import config_file_option
from .options import components_option
from .options import component_types_option
from .options import environment_option
from .options import exclude_components_option
from .options import validate_project
from .options import verbose_option

from .utils import info
from .utils import error
from .utils import success


@click.version_option(version=__version__)
@click.group()
def main():
    """Give more power to Terraform."""
    pass


@click.argument('component', type=str)
@click.argument('project', type=str)
@main.command('init')
def init(project, component):
    """Initialize a Terraform component"""
    projects_dir = './projects'

    proj_dir = os.path.join(projects_dir, project)
    if not os.path.exists(proj_dir):
        info(f'Creating project at {proj_dir}...')
        os.makedirs(proj_dir)

    comp_dir = os.path.join(proj_dir, component)
    if os.path.exists(comp_dir):
        error(f'Component {component} already exists for {project} project')
        sys.exit(1)

    info(f'Creating component at {comp_dir}...')
    os.makedirs(comp_dir)

    tf_common_files = [f for f in os.listdir(projects_dir) if f.endswith('.tf')]
    if tf_common_files:
        info('Found .tf file(s) in projects dir. Creating symlinks...')

        for tf_file in tf_common_files:
            src = os.path.relpath(os.path.join(projects_dir, tf_file), comp_dir)
            dest = os.path.join(comp_dir, tf_file)

            os.symlink(src, dest)

    success('Done!')



@config_file_option()
@main.command('projects')
def projects_cmd(config):
    """Display available projects in your configuration."""
    p_names = config['projects'].keys()

    info('Available projects:')
    for p_name in p_names:
        info('- %s' % p_name)


@config_file_option()
@component_types_option()
@click.argument('project', type=str)
@main.command('components')
def components_cmd(project, component_types, config):
    """Display available components for a project in your configuration."""
    project = validate_project(project, config)
    p_components = parse_project_config(config, project)
    c_names = p_components.keys()

    if component_types:
        info('Available components for project "%s" of type(s) "%s":' % (project, ', '.join(component_types)))
    else:
        info('Available components for project "%s":' % project)

    for c_name in c_names:
        should_print = True

        if component_types:
            component_config = p_components[c_name]
            c_type = component_config.get('component_type', c_name)

            if c_type not in component_types:
                should_print = False

        if should_print:
            info('- %s' % c_name)


@verbose_option()
@exclude_components_option()
@component_types_option()
@components_option()
@config_file_option()
@click.option(
    'project',
    '-p',
    '--project',
    type=str,
    default='',
    help='Project to manage.',
)
@click.argument('packages', type=str, nargs=-1)
@main.command('install')
def install_cmd(packages, **kwargs):
    """Discover and downloads plugins from your components."""
    plugins_dir = get_plugins_dir()

    install_terraform_plugin(plugins_dir)

    if packages:
        manual_install(packages, plugins_dir)
    else:
        discover_and_install(plugins_dir, **kwargs)


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@environment_option()
@exclude_components_option()
@component_types_option()
@components_option()
@config_file_option()
@click.argument('project', type=str)
@main.command('plan', context_settings=dict(ignore_unknown_options=True))
def tf_plan_cmd(**kwargs):
    """Terraform plan command (https://www.terraform.io/docs/commands/plan.html)."""
    run(
        command='plan',
        **kwargs,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@component_types_option()
@components_option()
@click.argument('project', type=str)
@main.command('apply', context_settings=dict(ignore_unknown_options=True))
def tf_apply_cmd(**kwargs):
    """Terraform apply command (https://www.terraform.io/docs/commands/apply.html)."""
    run(
        command='apply',
        **kwargs,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@component_types_option()
@components_option()
@click.argument('project', type=str)
@main.command('destroy', context_settings=dict(ignore_unknown_options=True))
def tf_destroy_cmd(**kwargs):
    """Terraform destroy command (https://www.terraform.io/docs/commands/destroy.html)."""
    run(
        command='destroy',
        **kwargs,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@component_types_option()
@components_option()
@click.argument('project', type=str)
@main.command('refresh', context_settings=dict(ignore_unknown_options=True))
def tf_refresh_cmd(**kwargs):
    """Terraform refresh command (https://www.terraform.io/docs/commands/refresh.html)."""
    run(
        command='refresh',
        **kwargs,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@component_types_option()
@components_option()
@click.argument('project', type=str)
@main.command('validate', context_settings=dict(ignore_unknown_options=True))
def tf_validate_cmd(**kwargs):
    """Terraform validate command (https://www.terraform.io/docs/commands/validate.html)."""
    run(
        command='validate',
        **kwargs,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@click.argument('resource_id', type=str)
@click.argument('address', type=str)
@click.argument('component', type=str)
@click.argument('project', type=str)
@main.command('import', context_settings=dict(ignore_unknown_options=True))
def tf_import_cmd(component, **kwargs):
    """Terraform import command (https://www.terraform.io/docs/import/index.html)."""
    run(
        command='import',
        components=[component],
        **kwargs,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@config_file_option()
@environment_option()
@exclude_components_option()
@component_types_option()
@components_option()
@click.argument('project', type=str)
@click.argument('subcommand', type=click.Choice(['list', 'mv', 'pull', 'push', 'rm', 'show']))
@main.command('state', context_settings=dict(ignore_unknown_options=True))
def tf_state(subcommand, **kwargs):
    """Terraform state command (https://www.terraform.io/docs/commands/state/index.html)."""
    run(
        command=f'state {subcommand}',
        **kwargs,
    )


@click.argument('tf_args', nargs=-1, type=click.UNPROCESSED)
@verbose_option()
@environment_option()
@exclude_components_option()
@component_types_option()
@components_option()
@config_file_option()
@click.option(
    'project',
    '-p',
    '--project',
    type=str,
    help='Project to manage.',
)
@click.argument('output_name', type=str)
@main.command('output', context_settings=dict(ignore_unknown_options=True))
def tf_output_cmd(**kwargs):
    """Terraform output command (https://www.terraform.io/docs/commands/output.html)."""
    run(
        command=f'output',
        **kwargs,
    )


if __name__ == '__main__':
    main()
