import pytest

from stone_burner.config import parse_project_config
from stone_burner.config import get_component_paths

from .utils import SAMPLE_CONFIG


def test_parse_project_config_1():
    e = {
        'c1': {'component_type': 'c1', 'validate': {}},
        'c2': {'component_type': 'c2', 'validate': {}},
        'mg1': {'component_type': 'my-generic-component', 'validate': {}},
        'mg2': {'component_type': 'my-generic-component', 'validate': {}},
        'oc1': {'component_type': 'other-generic-component', 'validate': {}},
        'oc2': {'component_type': 'other-generic-component', 'validate': {}},
    }

    r = parse_project_config(SAMPLE_CONFIG, 'p1')

    assert r == e


def test_parse_project_config_2():
    with pytest.raises(Exception):
        parse_project_config(SAMPLE_CONFIG, 'p2')


def test_get_component_paths_1():
    r = get_component_paths(
        'p1', 'c1', {'component_type': 'gc'}, 'e1', '/tmp/states', '/tmp/projects', '/tmp/vars')

    e = {
        'config_dir': '/tmp/projects/p1/gc',
        'vars_file': '/tmp/vars/e1/p1/c1.tfvars',
        'state_dir': '/tmp/states/e1/p1/c1',
    }

    assert r == e
