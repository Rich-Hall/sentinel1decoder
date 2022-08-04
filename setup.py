from distutils.core import setup

setup(
  name='sentinel1Decoder',
  url='https://github.com/Rich-Hall/sentinel1decoder',
  author='Rich Hall',
  author_email='richardhall434@gmail.com',
  packages='sentinel1decoder',
  install_requires=['numpy', 'pandas'],
  version='0.1',
  license='GPL-3.0',
  description='A python decoder for ESA Sentinel-1 Level0 files',
  long_description=open('README.md').read()
)
