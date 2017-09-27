from setuptools import find_packages
from setuptools import setup

import stone_burner

setup(
    name='stone-burner',
    version='0.1',
    description=stone_burner.__doc__.strip(),
    packages=find_packages(),
    install_requires=[
        'jinja2==2.9',
        'pyyaml==3.12',
        'click==6.7',
        'crayons==0.1.2',
    ],
    entry_points={
        'console_scripts': [
            'stone-burner = stone_burner:main',
        ],
    },
)
