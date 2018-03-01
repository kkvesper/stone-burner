import os
import subprocess

from stone_burner.lib import run
from stone_burner.lib import check_validation

from .utils import SAMPLE_CONFIG


def test_run_1(monkeypatch):
    """Test run does not crash."""
    monkeypatch.setattr(subprocess, 'check_call', lambda cmd: True)
    monkeypatch.setattr(os, 'chdir', lambda path: True)

    run(
        command='plan',
        project='p1',
        components=['c1', 'c2', 'c3'],
        exclude_components=[],
        environment='e1',
        config=SAMPLE_CONFIG,
        tf_args=[],
        verbose=0,
    )


def test_check_validation_1(monkeypatch):
    monkeypatch.setattr(os.path, 'exists', lambda path: True)
    r = check_validation('p1', 'c1', 'e1', {'component_type': 'ct1', 'validate': {}})

    assert r is True


def test_check_validation_2(monkeypatch):
    monkeypatch.setattr(os.path, 'exists', lambda path: True)
    r = check_validation('p1', 'c1', 'e1', {'component_type': 'ct1', 'validate': {'skip': True}})

    assert r is False


def test_check_validation_3(monkeypatch):
    monkeypatch.setattr(os.path, 'exists', lambda path: False)
    r = check_validation('p1', 'c1', 'e1', {'component_type': 'ct1', 'validate': {}})

    assert r is False
