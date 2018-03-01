import pytest

from stone_burner.config import parse_project_config
from stone_burner.config import TFAttributes
from stone_burner.config import get_component_paths

from .utils import SAMPLE_CONFIG


def test_parse_project_config_1():
    e = {
        'c1': {'component_type': 'c1', 'validate': {}},
        'c2': {'component_type': 'c2', 'validate': {}},
        'c3': {'component_type': 'c3', 'validate': {'check-variables': False}},
        'mg1': {'component_type': 'my-generic-component', 'validate': {}},
        'mg2': {'component_type': 'my-generic-component', 'validate': {}},
        'mg3': {'component_type': 'my-generic-component', 'validate': {'check-variables': False}},
        'oc1': {'component_type': 'other-generic-component', 'validate': {}},
        'oc2': {'component_type': 'other-generic-component', 'validate': {}},
    }

    r = parse_project_config(SAMPLE_CONFIG, 'p1')

    assert r == e


def test_parse_project_config_2():
    with pytest.raises(Exception):
        parse_project_config(SAMPLE_CONFIG, 'p2')

    def check_variables(*args, **kwargs):
        component_config = kwargs['component_config']
        validate_config = component_config.get('validate', {})
        check_variables = validate_config.get('check-variables', True)

        return ['true'] if check_variables else ['false']


def test_TFAttributes_check_variables_1():
    tf_attrs = TFAttributes()
    r = tf_attrs.check_variables(
        component_config={'component_type': 'c3', 'validate': {'check-variables': True}})

    assert r == ['true']


def test_TFAttributes_check_variables_2():
    tf_attrs = TFAttributes()
    r = tf_attrs.check_variables(
        component_config={'component_type': 'c3', 'validate': {'check-variables': False}})

    assert r == ['false']


def test_TFAttributes_check_variables_3():
    tf_attrs = TFAttributes()
    r1 = tf_attrs.check_variables(
        component_config={'component_type': 'c3'})

    assert r1 == ['true']

    r2 = tf_attrs.check_variables(
        component_config={'component_type': 'c3', 'validate': {}})

    assert r2 == ['true']

    r3 = tf_attrs.check_variables(
        component_config={'component_type': 'c3', 'validate': None})

    assert r3 == ['true']


def test_get_component_paths_1():
    r = get_component_paths(
        'p1', 'c1', {'component_type': 'gc'}, 'e1', '/tmp/states', '/tmp/projects', '/tmp/vars')

    e = {
        'config_dir': '/tmp/projects/p1/gc',
        'vars_file': '/tmp/vars/e1/p1/c1.tfvars',
        'state_dir': '/tmp/states/e1/p1/c1',
    }

    assert r == e
