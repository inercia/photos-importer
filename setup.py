from setuptools import setup

setup(name='photos_importer',
      version='0.1',
      packages=['photos_importer'],
      entry_points={
          'console_scripts': [
              'photos_importer = photos_importer.__main__:main'
          ]
      },
      )
