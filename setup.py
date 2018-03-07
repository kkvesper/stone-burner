# -*- coding: utf-8 -*-

from setuptools import find_packages
from setuptools import setup

from stone_burner import __version__

setup(
    name='stone-burner',
    version=__version__,
    description='Give more power to Terraform.',
    author='Rodrigo Argüello Flores',
    author_email='rodrigo@kkvesper.jp',
    url='https://github.com/kkvesper/stone-burner',
    download_url='https://github.com/kkvesper/stone-burner/archive/v%s.tar.gz' % __version__,
    packages=find_packages(),
    install_requires=[
        'jinja2>=2.9',
        'pyyaml>=3.12',
        'click>=6.7',
        'crayons>=0.1.2',
    ],
    entry_points={
        'console_scripts': [
            'stone-burner = stone_burner.cli:main',
        ],
    },
    keywords=['terraform', 'planetary-annihilation', 'infrastructure-as-code'],
)
