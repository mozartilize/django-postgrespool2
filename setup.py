#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
from django_postgrespool2 import __version__, __author__

required = [
    'sqlalchemy>=1.2',
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
    packages=['django_postgrespool2'],
    install_requires=required,
    license='MIT',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
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
