#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import shutil
import sys

from setuptools import setup

name = 'drf-spectacular'
package = 'drf_spectacular'
description = 'Sane and flexible OpenAPI 3 schema generation for Django REST framework'
url = 'https://github.com/tfranzel/drf-spectacular'
author = 'T. Franzel'
author_email = 'tfranzel@gmail.com'
license = 'BSD'

with open('README.rst') as readme:
    long_description = readme.read()

with open('requirements/base.txt') as fh:
    requirements = [r for r in fh.read().split('\n') if not r.startswith('#')]


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("^__version__ = ['\"]([^'\"]+)['\"]",
                     init_py, re.MULTILINE).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath for dirpath, dirnames, filenames in os.walk(package)
        if os.path.exists(os.path.join(dirpath, '__init__.py'))
    ]


version = get_version(package)


if sys.argv[-1] == 'publish':
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit(1)
    os.system("python setup.py sdist bdist_wheel")
    if os.system("twine check dist/*"):
        print("twine check failed. Packages might be outdated.")
        print("Try using `pip install -U twine wheel`.\nExiting.")
        sys.exit(1)
    if os.system("twine upload dist/*"):
        print("failed to upload package")
        sys.exit(1)
    if os.environ.get('CI'):
        os.system("git config user.name github-actions")
        os.system("git config user.email github-actions@github.com")
    os.system(f"git tag -a {version} -m 'version {version}'")
    if os.system("git push --tags"):
        print("failed pushing release tag")
        sys.exit(1)
    shutil.rmtree('dist')
    shutil.rmtree('build')
    shutil.rmtree('drf_spectacular.egg-info')
    sys.exit()


setup(
    name=name,
    version=version,
    url=url,
    license=license,
    description=description,
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author=author,
    author_email=author_email,
    packages=get_packages(package),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=requirements,
    extras_require={
        "offline": ["drf-spectacular-sidecar"],
        "sidecar": ["drf-spectacular-sidecar"],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Documentation',
        'Topic :: Software Development :: Code Generators',
    ],
    project_urls={
        'Source': 'https://github.com/tfranzel/drf-spectacular',
        'Documentation': 'https://drf-spectacular.readthedocs.io',
    },
)
