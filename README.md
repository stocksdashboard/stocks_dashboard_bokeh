[![build status](
  http://img.shields.io/travis/stocksdashboard/stocks_dashboard_bokehmaster.svg?style=flat)](
 https://travis-ci.org/stocksdashboard/stocks_dashboard_bokeh)

# Stocks Dashboard in Bokeh
stocks_dashboard_bokeh builds a dashboard of stocks using the python library [bokeh](https://bokeh.pydata.org).

You need Python 3.6 or later to run `stocksdhasboard`.


![Preview of StocksDashboard](dashboard.jpg)

## To create a clean virtual environment on Mac OSX:

`virtualenv --no-site-packages -p python3 venv`

## To install the dependencies:
`pip install -r requirements.txt`

## To run bokeh server:
`bokeh serve --show sdb/main.py` 

## Resources
- [Bokeh](https://bokeh.pydata.org).
