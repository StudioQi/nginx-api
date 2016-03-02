#!/usr/bin/env python

from distutils.core import setup
from glob import glob

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name='nginx_api',
      version='0.5.2',
      description='API to configure NGINX',
      author='Pierre Paul Lefebvre',
      author_email='info@pierre-paul.com',
      install_requires=required,
      url='https://jeto.io',
      packages=['nginx_api'],
      include_package_data=True
)
