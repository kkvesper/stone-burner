import os
import stat
import subprocess
import shutil
import tempfile
import platform
import zipfile

from urllib.request import urlopen

from .config import parse_project_config
from .config import get_component_paths

from .options import validate_project
from .options import validate_components

from .utils import info
from .utils import success
from .utils import error
from .utils import exec_command


# 0755
PLUGIN_PERMISSIONS = (
    stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
    stat.S_IRGRP | stat.S_IXGRP |
    stat.S_IROTH | stat.S_IXOTH
)


def install_terraform_plugin(plugin_dir, plugin_permissions=PLUGIN_PERMISSIONS):
    info('Installing terraform provider plugin from terraform binary...')

    for plugin in os.listdir(plugin_dir):
        if plugin.startswith('terraform-provider-terraform'):
            # Remove previous terraform plugin
            os.remove(os.path.join(plugin_dir, plugin))

    tf_bin = subprocess.check_output(
        ['which', 'terraform']).decode().split('\n')[0]
    tf_version = subprocess.check_output(
        ['terraform', '-v']).decode().split('\n')[0].split(' ')[1]

    info('Found terraform at %s on version: %s' % (tf_bin, tf_version))

    tf_plugin_name = 'terraform-provider-terraform_%s_x4' % tf_version
    tf_plugin_path = os.path.join(plugin_dir, tf_plugin_name)

    info('Installing %s on %s' % (tf_plugin_name, plugin_dir))
    shutil.copy2(tf_bin, tf_plugin_path)
    os.chmod(tf_plugin_path, plugin_permissions)
    success('OK!')


def manual_install(packages, plugin_dir, plugin_permissions=PLUGIN_PERMISSIONS):
    suffix = ''
    system = platform.system()

    if system == 'Darwin':
        suffix = 'darwin_amd64'
    elif system == 'Linux':
        machine = platform.machine()

        if machine == 'x86_64':
            suffix = 'linux_amd64'
        elif machine == 'i386':
            suffix = 'linux_386'
        else:
            raise Exception('Unsupported Linux architecture: %s' % machine)
    else:
        raise Exception('Unsupported distribution: %s' % system)

    base_url = 'https://releases.hashicorp.com/'

    temp_dir = tempfile.mkdtemp()

    for pkg in packages:
        info('Installing %s...' % pkg)
        try:
            name, version = pkg.split('@')
        except ValueError:
            error('Bad syntax: %s.' % pkg)
            error(
                'Packages must be specified with the following syntax: <name>@<version>')
        else:
            fname = 'terraform-provider-%s_%s_%s.zip' % (
                name, version, suffix)
            url = os.path.join(
                base_url, 'terraform-provider-%s' % name, version, fname)
            dest_file = os.path.join(temp_dir, fname)

            info('downloading %s...' % url)
            try:
                with urlopen(url) as response, open(dest_file, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
            except Exception:
                import traceback
                error('An error ocurred downloading %s' % url)
                error(traceback.format_exc())
            else:
                info('Extracting %s to %s...' % (fname, plugin_dir))
                zip_ref = zipfile.ZipFile(dest_file, 'r')
                zip_ref.extractall(plugin_dir)
                zip_ref.close()
                success('OK!')

    shutil.rmtree(temp_dir)
    info('Setting plugin permissions...')
    for f in os.listdir(plugin_dir):
        os.chmod(os.path.join(plugin_dir, f), plugin_permissions)

    success('OK!')


def discover_and_install(
    plugins_dir, project, components, config, component_types=[], exclude_components=[], verbose=0, *args, **kwargs
):
    project = validate_project(project, config)
    p_components = parse_project_config(config, project)

    if component_types:
        p_components = {
            c: p_components[c]
            for c in p_components
            if p_components[c]['component_type'] in component_types
        }

        if not p_components:
            raise Exception(
                "There isn't any component belonging to the specified types")

        components = [
            c
            for c in list(p_components.keys())
            if c in components
        ]

    if components:
        components = validate_components(components, p_components)
    else:
        # If no component is chosen, use all of them
        components = list(p_components.keys())

    components = list(set(components) - set(exclude_components))

    workdir = os.getcwd()

    for component in components:
        component_config = p_components[component] or {}
        c_paths = get_component_paths(project, component, component_config, '')
        config_dir = c_paths['config_dir']

        os.chdir(config_dir)

        temp_dir = tempfile.mkdtemp()

        exec_command(
            cmd=['terraform', 'init', '-backend=false', '-get=true', '-get-plugins=true', '-input=false'],
            tf_data_dir=temp_dir,
        )

        for root, _, filenames in os.walk(os.path.join(temp_dir, 'plugins')):
            for f_name in filenames:
                f_path = os.path.join(root, f_name)

                if f_name != 'lock.json':
                    # TODO: keep json.lock file and merge new ones
                    shutil.move(f_path, os.path.join(plugins_dir, f_name))

        shutil.rmtree(temp_dir)
        os.chdir(workdir)
