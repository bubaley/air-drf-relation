from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='drf_irelation',
      version='0.0.4',
      description='Improved interaction with DRF relations.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      keywords='django rest relation nested pk primary object',
      url='https://github.com/justjew/irelation',
      author='justjew',
      author_email='justjew1406@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'djangorestframework',
      ],
      include_package_data=True,
      zip_safe=False)
