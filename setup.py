# Py3plex installation file. Cython code for fa2 is the courtesy of Bhargav Chippada.
# https://github.com/bhargavchippada/forceatlas2

from os import path
import sys
from setuptools import setup, find_packages
from setuptools.extension import Extension

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file

if "--cpp" in sys.argv:

    if path.isfile(path.join(here, 'py3plex/visualization/fa2/fa2util.c')):
        print("Using existing visualization engine..")
        # cython build locally and add fa2/fa2util.c to MANIFEST or fa2.egg-info/SOURCES.txt
        # run: python setup.py build_ext --inplace
        ext_modules = [
            Extension('fa2.fa2util', ['py3plex/visualization/fa2/fa2util.c'])
        ]
        cmdclass = {}
        cythonopts = {"ext_modules": ext_modules, "cmdclass": cmdclass}
    else:

        print("Compiling the visualization engine..")
        cythonopts = None

        # Uncomment the following line if you want to install without optimizations
        # cythonopts = {"py_modules": ["fa2.fa2util"]}

        try:
            if cythonopts is None:
                from Cython.Build import build_ext

                ext_modules = [
                    Extension('fa2.fa2util', [
                        'py3plex/visualization/fa2/fa2util.py',
                        'py3plex/visualization/fa2/fa2util.pxd'
                    ])
                ]
                cmdclass = {'build_ext': build_ext}
                cythonopts = {"ext_modules": ext_modules, "cmdclass": cmdclass}
        except:

            print(
                "Installing without optimizations.. Please install gcc for better performance!"
            )
            cythonopts = {"py_modules": ["py3plex/visualization/fa2.fa2util"]}

    sys.argv.remove("--cpp")
else:
    cythonopts = {"py_modules": ["py3plex/visualization/fa2.fa2util"]}


def parse_requirements(file):
    required_packages = []
    with open(path.join(path.dirname(__file__), file)) as req_file:
        for line in req_file:
            required_packages.append(line.strip())
    return required_packages


setup(name='py3plex',
      version='0.82',
      description="A Multilayer network analysis python3 library",
      url='http://github.com/skblaz/py3plex',
      python_requires='>3.6.0',
      author='Blaž Škrlj',
      author_email='blaz.skrlj@ijs.si',
      license='MIT',
      packages=find_packages(),
      install_requires=parse_requirements("requirements.txt"),
      zip_safe=False,
      include_package_data=True,
      **cythonopts)
