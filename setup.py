try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='StocksDashboard',
    version='0.1dev0',
    description='A package to build Stocks Dashboards in Bokeh',
    author='Mabel Villalba, Emilio Molina',
    author_email="mabelvj@gmail.com, emilio.mol.mar@gmail.com",
    keywords=['bokeh', 'stocks', 'dashboard'],
    packages=['sdb', ],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    url='https://github.com/stocksdashboard/stocks_dashboard_bokeh',
    install_requires=requirements,
    # long_description=open('README.txt').read(),
)
