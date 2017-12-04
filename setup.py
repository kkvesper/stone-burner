from setuptools import find_packages
from setuptools import setup

setup(
    name='stone-burner',
    version='0.1',
    description='Give more power to Terraform.',
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
)
