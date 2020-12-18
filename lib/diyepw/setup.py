import setuptools  # pragma: no cover

setuptools.setup(  # pragma: no cover
      name='diyepw',
      version='1.0',
      description='A package offering support for generating EPW (EnergyPlus Weather) files',
      url='https://github.com/IMMM-SFA/diyepw',
      author='Amanda Smith',
      author_email='amanda.d.smith@pnnl.gov',
      packages=setuptools.find_packages(),
      python_requires='~=3.7',
      install_requires=[
          'numpy~=1.19',
          'pandas~=1.1',
          'xarray~=0.16.2'
      ]
)
