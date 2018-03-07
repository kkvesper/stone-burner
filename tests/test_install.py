import os
import subprocess
import shutil
import platform
import tempfile
import zipfile
import builtins
import urllib.request

from stone_burner.install import install_terraform_plugin
from stone_burner.install import manual_install
from stone_burner.install import discover_and_install

from .utils import SAMPLE_CONFIG


def test_install_terraform_plugin_1(monkeypatch):
    """Test install_terraform_plugin does not crash."""
    monkeypatch.setattr(os, 'listdir', lambda path: [
                        'terraform-provider-terraform_v0.11.2_x4'])
    monkeypatch.setattr(os, 'remove', lambda path: True)
    monkeypatch.setattr(os, 'chmod', lambda path, permissions: True)

    monkeypatch.setattr(shutil, 'copy2', lambda src, dest: True)

    def mp_check_output(cmd):
        if cmd == ['which', 'terraform']:
            return b'/usr/local/bin/terraform\n'

        if cmd == ['terraform', '-v']:
            return b'Terraform v0.11.3\n\n'

        raise Exception('Unmocked command: %s' % cmd)

    monkeypatch.setattr(subprocess, 'check_output', mp_check_output)

    install_terraform_plugin('/tmp/stone-burner_plugins')


def test_manual_install_1(monkeypatch):
    """Test manual_install does not crash."""

    monkeypatch.setattr(platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(platform, 'machine', lambda: 'x86_64')
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: '/tmp/tempdir')
    monkeypatch.setattr(shutil, 'rmtree', lambda path: True)
    monkeypatch.setattr(shutil, 'copyfileobj', lambda src, dest: True)
    monkeypatch.setattr(os, 'listdir', lambda path: [
                        'terraform-provider-terraform_v0.11.2_x4', 'pkg1', 'pkg2'])
    monkeypatch.setattr(os, 'chmod', lambda path, permissions: True)

    def mp_zip_file(dest, mode):
        class MockedZipFile:
            def extractall(self, dest):
                return True

            def close(self):
                return True

        return MockedZipFile()

    def mp_url_open(url):
        class MockedUrlOpen:
            def __enter__(self):
                return 'content'

            def __exit__(self, type, value, traceback):
                pass

        return MockedUrlOpen()

    def mp_open(file, mode):
        class MockedOpen:
            def __enter__(self):
                return 'content'

            def __exit__(self, type, value, traceback):
                pass

        return MockedOpen()

    monkeypatch.setattr(urllib.request, 'urlopen', mp_url_open)
    monkeypatch.setattr(builtins, 'open', mp_open)

    monkeypatch.setattr(zipfile, 'ZipFile', mp_zip_file)

    manual_install(['pkg1@1.0.2', 'pkg2'], '/tmp/stone-burner_plugins')


def test_discover_and_install_1(monkeypatch):
    """Test discover_and_install does not crash."""
    monkeypatch.setattr(subprocess, 'check_call', lambda cmd: True)
    monkeypatch.setattr(os, 'getcwd', lambda: '/tmp')
    monkeypatch.setattr(os, 'chdir', lambda path: True)
    monkeypatch.setattr(os, 'walk', lambda path: [
                        ('root', ['d1', 'd2'], ['f1', 'f2']), ])
    monkeypatch.setattr(tempfile, 'mkdtemp', lambda: '/tmp/tempdir')
    monkeypatch.setattr(shutil, 'move', lambda src, dest: True)
    monkeypatch.setattr(shutil, 'rmtree', lambda path: True)

    discover_and_install(
        '/tmp/stone-burner_plugins',
        'p1',
        ['c1', 'c2', 'c3'],
        SAMPLE_CONFIG,
        ['c1', 'c2'],
    )
