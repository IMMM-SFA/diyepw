"""
Setup file for DIYEPW
:author:   Amanda Smith
:email:    amanda.d.smith@pnnl.gov
License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
"""

import setuptools  # pragma: no cover

def readme():
    with open('README.md') as f:
        return f.read()

def get_requirements():
    with open('requirements.txt') as f:
        return f.read().split()

setuptools.setup(  # pragma: no cover
      name='diyepw',
      version='1.0',
      description='A package offering support for generating EPW (EnergyPlus Weather) files',
      long_description=readme(),
      long_description_content_type="text/markdown",
      url='https://github.com/IMMM-SFA/diyepw',
      author='Amanda Smith',
      author_email='amanda.d.smith@pnnl.gov',
      packages=setuptools.find_packages(),
      package_data={ 'diyepw': ['data/**/*', 'test/files/**/*'] },
      license='BSD 2-Clause',
      python_requires='~=3.7',
      install_requires=get_requirements(),
      extras_require={
          'dev': [
              'pvlib~=0.8.1'
          ]
      }
)
