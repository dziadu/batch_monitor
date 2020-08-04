"""
django-jquery-file-uploader
"""
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test

#def run_tests(*args):
    #from filterjs.tests import run_tests
    #errors = run_tests()
    #if errors:
        #sys.exit(1)
    #else:
        #sys.exit(0)

#test.run_tests = run_tests

setup(
    name="django-batch-farm-monitor",
    version="0.0.3",
    packages=['batch_farm_monitor'],
    license="The MIT License (MIT)",
    include_package_data = True,
    description=("batch-farm-monitor"),
    long_description=("A Django app for batch-farm-monitor: "
                "https://github.com/rlalik/batch-farm-monitor"),
    author="Rafal Lalik",
    author_email="rafallalik@gmail.com",
    maintainer="Rafal Lalik",
    maintainer_email="rafallalik@gmail.com",
    url="https://github.com/rlalik/django-batch-farm-monitor/",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Framework :: Django',
    ],
    test_suite="dummy",
)
