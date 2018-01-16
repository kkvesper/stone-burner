
import pytest
import click

from stone_burner.options import validate_components
from stone_burner.options import validate_environment

from utils import SAMPLE_CONFIG


def test_validate_components_1():
    e = ['c1', 'c2', 'oc1']
    r = validate_components(['c1', 'c2', 'oc1'], 'p1', SAMPLE_CONFIG)

    assert len(r) == len(e) and sorted(r) == sorted(e)


def test_validate_components_2():
    with pytest.raises(click.BadParameter):
        validate_components(['c1', 'c2', 'oc1', 'ne-c'], 'p1', SAMPLE_CONFIG)


def test_validate_environment_1():
    assert 'e1' == validate_environment('e1', SAMPLE_CONFIG)


def test_validate_environment_2():
    with pytest.raises(click.BadParameter):
        validate_environment('e3', SAMPLE_CONFIG)
