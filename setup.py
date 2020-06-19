from setuptools import setup, find_packages


setup(name='irelation',
      version='0.1',
      description='Improved interaction with DRF relations.',
      long_description='This package helps you to easily set object\'s relation from API request.',
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
