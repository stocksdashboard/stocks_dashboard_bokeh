from .stocksdashboard import StocksDashboard
from .stocksdashboard import convert_to_datetime
from .stocksdashboard import get_colors
from .formatter import Formatter
from .dashboard_with_widgets import DashboardWithWidgets

import sys
import os
from os.path import dirname

if sys.version_info[0] < 3:
    from ConfigParser import SafeConfigParser
else:
    from configparser import SafeConfigParser

__all__ = ['StocksDashboard', 'convert_to_datetime', 'get_colors', 'Formatter',
           'DashboardWithWidgets']

config = SafeConfigParser()
path = config.read(os.path.join(os.path.abspath(
    dirname(__file__)), 'config.ini'))
config.read(path)
__author__ = config['main']['AUTHORS']
__license__ = config['main']['LICENSE']
__version__ = config['main']['VERSION']
