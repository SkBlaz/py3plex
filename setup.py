## added setup

from setuptools import setup,find_packages

setup(name='py3plex',
      version='0.02',
      description="A Multilayer network analysis python3 library",
      url='http://github.com/skblaz/py3plex',
      author='Blaž Škrlj',
      author_email='blaz.skrlj@ijs.si',
      license='MIT',
      packages=find_packages(),
      zip_safe=False)
      # packages=['py3plex',
      #           'py3plex.visualization',
      #           'py3plex.core',
      #           'py3plex.wrappers',
      #           'py3plex.algorithms',
      #           'py3plex.core.HINMINE'],
