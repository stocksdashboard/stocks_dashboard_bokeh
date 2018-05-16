import os


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration

    libraries = []
    if os.name == 'posix':
        libraries.append('m')

    config = Configuration('stocksdashboard', parent_package, top_path)

    # the following packages depend on cblas, so they have to be build
    # after the above.
    # config.add_subpackage('utils')

    # add the test directory
    config.add_subpackage('tests')

    return config


if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
