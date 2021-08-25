"""
Setup file for DIYEPW
:author:   Amanda Smith
:email:    amanda.d.smith@pnnl.gov
License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
"""

import setuptools  # pragma: no coverU


def readme():
    with open('README.md') as f:
        return f.read()


setuptools.setup(  # pragma: no cover
      name='diyepw',
      description='A package offering support for generating EPW (EnergyPlus Weather) files',
      long_description=readme(),
      long_description_content_type="text/markdown",
      url='https://github.com/IMMM-SFA/diyepw',
      author='Amanda Smith',
      author_email='amanda.d.smith@pnnl.gov',
      packages=setuptools.find_packages(),
      package_data={'diyepw': ['data/**', 'test/files/**', 'data/**/*', 'test/files/**/*']},
      license='BSD 2-Clause',
      python_requires='~=3.7',
      install_requires=[
          'click~=8.0.1',
          'numpy~=1.21.2',
          'pandas~=1.3.2',
          'pvlib~=0.8.1',
          'xarray~=0.19.0',
      ],
      extras_require={
          'dev': [
              'build>=0.5.1',
              'pytest~=6.2.4',
              'twine~=3.4.1',
              'recommonmark~=0.7.1',
              'setuptools~=57.0.0',
              'sphinx~=3.5.1',
              'sphinx-rtd-theme~=0.5.1',
          ]
      },
      entry_points={
          'console_scripts': [
              'analyze_noaa_data = diyepw.scripts.analyze_noaa_data:analyze_noaa_data',
              'create_amy_epw_files = diyepw.scripts.create_amy_epw_files:create_amy_epw_files',
              'create_amy_epw_files_for_years_and_wmos = diyepw.scripts.create_amy_epw_files_for_years_and_wmos:create_amy_epw_files_for_years_and_wmos',
          ],
      },
)
