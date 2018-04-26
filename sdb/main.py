"""
    Example of usage.
    To run do in the command line: bokeh serve main.py
"""

import numpy as np
import pandas as pd
from stocksdashboard import StocksDashboard
from bokeh.sampledata.stocks import AAPL, GOOG, IBM, MSFT


window_size = 30
window = np.ones(window_size) / float(window_size)
aapl = np.array(AAPL['adj_close'])
aapl_dates = np.array(AAPL['date'], dtype=np.datetime64)
aapl_avg = pd.DataFrame([aapl_dates,
                         np.convolve(aapl, window, 'same')],
                        index=['date', 'adj_close']).T
"""StocksDashboard().build_dashboard(data1={'AAPL': AAPL, 'GOOG': GOOG,
                                         'IBM': IBM, 'MSFT': MSFT},
                                  data2={'AAPL_avg': aapl_avg},
                                  params={'line_width': 2, 'color': 'pink'},
                                  params2={'line_width': 1.5})"""

# Multiple formats for each line.
StocksDashboard().build_dashboard(data1={'AAPL': AAPL, 'GOOG': GOOG,
                                         'IBM': IBM, 'MSFT': MSFT},
                                  data2={'AAPL_avg': aapl_avg},
                                  params={'GOOG': {'line_dash': 'dashed'},
                                          'AAPL': {'color': 'blue'}},
                                  params2={'color': 'orange',
                                           'line_width': 1.5},
                                  line_width=2)
