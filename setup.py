#! /usr/bin/env python

"""To build the package run:
>>> python setup.py bdist_wheel --universal

To upload it to pypitest:
>>> twine upload --repository-url https://test.pypi.org/legacy/ dist/*

>> pip install --index-url https://test.pypi.org/simple/ StocksDashboard
"""
import sys
import os
from os.path import dirname
import shutil
from distutils.command.clean import clean as Clean

if sys.version_info[0] < 3:
    import __builtin__ as builtins
    from ConfigParser import SafeConfigParser
else:
    import builtins
    from configparser import SafeConfigParser

config = SafeConfigParser()
path = config.read(os.path.join(os.path.abspath(
    dirname(__file__)), 'stocksdashboard', 'config.ini'))
config.read(path)  # All info about version and is there.
# MAINTAINER = "Mabel Villalba Jimenez"
# MAINTAINER_EMAIL = "mabelvj@gmail.com"
# VERSION = '0.10dev0'
# LICENSE = 'Creative Commons Attribution-Noncommercial-Share Alike license'
MAINTAINER = config['main']['MAINTAINER']
MAINTAINER_EMAIL = config['main']['MAINTAINER_EMAIL']
LICENSE = config['main']['LICENSE']
VERSION = config['main']['VERSION']
print(VERSION)


class CleanCommand(Clean):
    description = "Remove build artifacts from the source tree"

    def run(self):
        Clean.run(self)
        # Remove c files if we are not within a sdist package
        cwd = os.path.abspath(os.path.dirname(__file__))
        remove_c_files = not os.path.exists(os.path.join(cwd, 'PKG-INFO'))
        if remove_c_files:
            print('Will remove generated .c files')
        if os.path.exists('build'):
            shutil.rmtree('build')
        for dirpath, dirnames, filenames in os.walk('stocksdashboard'):
            for filename in filenames:
                if any(filename.endswith(suffix) for suffix in
                       (".so", ".pyd", ".dll", ".pyc")):
                    os.unlink(os.path.join(dirpath, filename))
                    continue
                # extension = os.path.splitext(filename)[1]
                # if remove_c_files and extension in ['.c', '.cpp']:
                #     pyx_file = str.replace(filename, extension, '.pyx')
                #     if os.path.exists(os.path.join(dirpath, pyx_file)):
                #         os.unlink(os.path.join(dirpath, filename))
            for dirname in dirnames:
                if dirname == '__pycache__':
                    shutil.rmtree(os.path.join(dirpath, dirname))


cmdclass = {'clean': CleanCommand}


def setup_package():
    metadata = dict(
        name='stocksdashboard',
        version=VERSION,
        description='A package to build Stocks Dashboards in Bokeh',
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        author='%s, Emilio Molina Martinez' % MAINTAINER,
        author_email="%s, emilio.mol.mar@gmail.com" % MAINTAINER_EMAIL,
        keywords=['bokeh', 'stocks', 'dashboard'],
        packages=['stocksdashboard', ],
        license=LICENSE,
        url='https://github.com/stocksdashboard/stocks_dashboard_bokeh',
        # install_requires=requirements,
        cmdclass=cmdclass,
        # long_description=open('README.txt').read(),
        include_package_data=True,
        package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['config.ini'],}
        ,
    )
    # if len(sys.argv) == 1 or (
    #         len(sys.argv) >= 2 and ('--help' in sys.argv[1:] or
    #                                 sys.argv[1] in ('--help-commands',
    #                                                 'egg_info',
    #                                                 '--version',
    #                                                 'clean'))):

    try:
        from setuptools import setup
    except ImportError:
        from distutils.core import setup

    with open('requirements.txt') as f:
        requirements = f.read().splitlines()
        metadata['install_requires'] = requirements

    setup(**metadata)


if __name__ == "__main__":
    setup_package()
