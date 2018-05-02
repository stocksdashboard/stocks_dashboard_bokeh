"""To build the package run:
>>> python setup.py bdist_wheel --universal

To upload it to pypitest:
>>> twine upload --repository-url https://test.pypi.org/legacy/ dist/*
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

MAINTAINER = "Mabel Villalba Jimenez"
MAINTAINER_EMAIL = "mabelvj@gmail.com"
setup(
    name='StocksDashboard',
    version='0.11dev0',
    description='A package to build Stocks Dashboards in Bokeh',
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    author='%s, Emilio Molina Martinez' % MAINTAINER,
    author_email="%s, emilio.mol.mar@gmail.com" % MAINTAINER_EMAIL,
    keywords=['bokeh', 'stocks', 'dashboard'],
    packages=['stocksdashboard', ],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    url='https://github.com/stocksdashboard/stocks_dashboard_bokeh',
    install_requires=requirements,
    # long_description=open('README.txt').read(),
)
