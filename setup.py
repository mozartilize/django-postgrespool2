#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from django_postgrespool2 import __version__, __author__

required = [
    'sqlalchemy>=1.1',
    'django>=1.8',
]

setup(
    name='django-postgrespool2',
    version=__version__,
    description='Postgres Connection Pooling for Django.',
    long_description=open('README.rst').read(),
    author=__author__,
    author_email='malexey1984@gmail.com',
    url='https://github.com/lcd1232/django-postgrespool2',
    packages=find_packages(),
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=required,
    license='MIT',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Topic :: Database',
    ),
)
