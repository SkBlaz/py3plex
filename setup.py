## added setup

from setuptools import setup

setup(name='py3plex',
      version='0.02',
      description='The funniest joke in the world',
      url='http://github.com/skblaz/py3plex',
      author='Blaž Škrlj',
      author_email='blaz.skrlj@ijs.si',
      license='MIT',
      packages=['py3plex',
                'py3plex.visualization',
                'py3plex.core',
                'py3plex.wrappers',
                'py3plex.algorithms',
                'py3plex.core.HINMINE'],
      zip_safe=False)
