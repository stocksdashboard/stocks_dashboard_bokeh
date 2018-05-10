#!/usr/bin/env python3
# Authors: Mabel Villalba Jimenez <mabelvj@gmail.com>,
#          Emilio Molina Martinez <emilio.mol.mar@gmail.com>
# License: GPLv3

try:
    from .formatter import Formatter
except Exception as excinfo:
    print(str(excinfo))
    from formatter import Formatter

import numpy as np
import pandas as pd
from bokeh.layouts import gridplot
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.models import Range1d
from bokeh.models import FactorRange

from bokeh.models import LinearAxis
from bokeh.models import Axis
from bokeh.core.properties import value
import warnings
import copy

from bokeh.models import HoverTool
from bokeh.io import curdoc
from bokeh.layouts import row, widgetbox

WIDTH = 1024
HEIGHT = 648


def convert_to_datetime(x):
    return np.array(x, dtype=np.datetime64)


def get_colors(number_of_colors, palette_name='Category20'):
    from bokeh.palettes import all_palettes
    url_palettes = 'https://bokeh.pydata.org/en/' + \
                   'latest/docs/reference/palettes.html'
    warnings.warn("""Using palette %s.
        For other palettes visit:
        %s""" % (palette_name, url_palettes))
    colors = all_palettes[palette_name][max(number_of_colors, 3)]
    return colors


class StocksDashboard():
    tooltips = [
        ('date', '$x{%F}'),
        ('value', '$y{0.000}')
    ]
    formatters = {
        '$x': 'datetime',
    }
    mode = 'vline'
    names = None
    datasources = []

    def __init__(self, width=WIDTH, height=HEIGHT, ncols=1):
        self.width = width
        self.height = height
        self.ncols = ncols
        self._check_variables()

    def _check_variables(self, varname=None):

        def _is_valid_type(__varname=None, __value=None):
            if not __value:
                msg = "'%s cannot be None.'" % __varname
                raise(ValueError(msg))
            elif not isinstance(__value, int):
                msg = "'%s cannot be of" % __varname + \
                      "type %s, must be 'int'" % type(__value)
                raise (TypeError(msg))
            else:
                return True

        if varname and hasattr(self, varname):
            return _is_valid_type(varname, getattr(self, varname))
        else:
            for _varname, _value in self.__dict__.items():
                if _varname in ['width', 'height', 'ncols']:
                    _is_valid_type(_varname, _value)

    @staticmethod
    def _create_hover(tooltips=[('date', '$x{%F}'), ('value', '@y{0.000}')],
                      formatters={'$x': 'datetime'}, mode='vline', **kwargs):
        hover = HoverTool(**kwargs)
        hover.tooltips = tooltips
        hover.formatters = formatters
        hover.mode = mode
        return hover

    def _update_params(self, params, kwargs={}, names=None, aligment={}):
        # TODO: remove kwargs parameter
        """
            Update the aesthetics for plotting. Combine params and kwargs.

            Parameters
            ----------
            params: dict or dict of dicts
                Dict with params or dict with names and params per name.
            kwargs: dict
                Dict with general params for plotting.
            names: list or sequence of strings, default None
                List of names to be plotted.
            aligment: dict of strings
                Contains the axis to be selected for the line. Values
                for each dict can be: ('left', 'right', None).

            Returns
            -------
            result: dict
                Dict containing the parameters to use in the plotting.
                For more details see :Examples:

            Examples
            --------

            If params does not contains names:
                - Combine them:
                >>> import StocksDashboard as sdb
                >>> sdb.update_params(params = {'line_style': 'dot',
                ...                             'color': 'blue'},
                ...                   kwargs = {'line_width': 1.5})
                {'color': 'blue', 'line_style': 'dot', 'line_width': 1.5}
            If params contains names:
                - Update each dict:
                >>> sdb.update_params(params = {'GOOGL': {'line_style': 'dot'},
                ...                             'AAPL' :{'color': 'blue'}},
                ...                   kwargs = {'line_width': 1.5},
                ...                   names = ['GOOGL', 'AAPL'])
                {'AAPL': {'color': 'blue', 'line_width': 1.5},
                'GOOGL': {'line_style': 'dot', 'line_width': 1.5}}
            If both ``params`` and ``kwargs`` are empty, ``kwargs``
            is returned.
                >>> sdb.update_params(params = {}, kwargs={})
                {}
        """
        if params or kwargs:
            if (not names or
                (names and not any([n in params for n in names])) and not
                    aligment):
                params.update(copy.deepcopy(kwargs))
            else:
                _initial_params = {}
                if params and not all([n in params for n in names]):
                    # Params has parameters but not especific params per name.
                    _initial_params = copy.deepcopy(kwargs)
                    # Override kwargs with params for the plot
                    _initial_params.update(copy.deepcopy(params))
                    params = {}
                else:
                    _initial_params = copy.deepcopy(kwargs)

                for i, n in enumerate(names):
                    if n in params:
                        params[n].update(copy.deepcopy(_initial_params))
                    else:
                        params[n] = copy.deepcopy(_initial_params)
            if aligment:
                # only with more than one element we need two axis.
                # In the other case, we just move to right the main axis.
                for n in names:
                    if aligment[n] is 'right':
                        params[n].update(
                            {'y_range_name': self.y_right_name})
        else:
            if aligment:
                params = {n: {'y_range_name': self.y_right_name}
                          for n in names if aligment[n] is 'right'}
            else:
                params = copy.deepcopy(kwargs)
        return params

    @staticmethod
    def _add_color_and_legend(params, legend='', color='black'):
        _params = copy.deepcopy(params)
        if 'legend' not in _params:
            _params['legend'] = value(legend)
        if 'color' not in _params:
            _params['color'] = color
        return _params

    def _get_params(self, params, name, color):
        """ Try to find specific parameters for a given name."""
        try:
            return self._add_color_and_legend(params[name], name, color)
        except (TypeError, KeyError):
            return self._add_color_and_legend(params, name, color)

    def __update_datasource(self, datasource, stock, column, name):
        """
            Update the object datasource with data from each stock.
        """
        x, y = Formatter._get_x_y(stock, column)
        datasource.add(name=name, data=y)
        if 'x' not in datasource.data:
            datasource.add(name='x', data=x)
        return datasource

    def get_y_limits(self, data, aligment):
        _min = None
        _max = None
        for i, (stockname, al) in enumerate(list(aligment.items())):
            if al == 'right':
                if _min:
                    _min = min(_min, np.nanmin(data[i]))
                else:
                    _min = np.nanmin(data[i])
                if _max:
                    _max = max(_max, np.nanmax(data[i]))
                else:
                    _max = np.nanmax(data[i])
        return _min, _max

    def _right_limits(self, p, data, aligment, params):

        try:
            # checks if 'right' is in aligment or not
            list(aligment.values()).index('right')
            if len(data) == 1:
                # There is only one element
                # and we want to align it to the right
                p.yaxis.visible = False
            y_limits_right = self.get_y_limits(data, aligment)
            self.y_right_name = 'y1'
            p.extra_y_ranges = {self.y_right_name:
                                Range1d(y_limits_right[0],
                                        y_limits_right[1])}

        except Exception as excinfo:
            # print(str(excinfo))
            pass
        return p

    def _plot_stock(self, data=None, names=None, p=None, column='adj_close',
                    title="Stock Closing Prices", ylabel='Price',
                    ylabel_right=None, add_hover=True,
                    params={}, aligment={}, height=None, **kwargs_to_bokeh):

        if not p:
            p = figure(x_axis_type="datetime", title=title,
                       sizing_mode='scale_both', plot_width=self.width)
            if height:
                p.plot_height = int(height * self.height)
                # print(int(height*self.height))
            p.grid.grid_line_alpha = 0.3
            p.x_range = self.x_range
            p.xaxis.axis_label = 'Date'
            p.yaxis.axis_label = ylabel
            p = self._right_limits(p, data, aligment, params)

        # data, names = Formatter().format_data(input_data)
        colors = get_colors(len(data))
        params = self._update_params(params=params, kwargs=kwargs_to_bokeh,
                                     names=names, aligment=aligment)

        p_to_hover = []
        __datasource = ColumnDataSource()
        for i, stock in enumerate(data):
            __datasource = self.__update_datasource(__datasource, stock,
                                                    column, names[i])
            _params = self._get_params(params, names[i], colors[i])
            _p = p.line(x='x', y=names[i], source=__datasource, **_params)
            p_to_hover.append(_p)

        assert(len(__datasource.data) == len(data) + 1), (
            "Number of elements used as source don't match " +
            "data dimension.")  # len(data) + 1 -> all data and the x-axis
        self.datasources.append(__datasource)

        assert(len(p_to_hover) == len(data)), "Number of Lines " + \
                                              "don't match data dimension."
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        if add_hover:
            hover = StocksDashboard._create_hover(self.tooltips,
                                                  self.formatters,
                                                  self.mode,
                                                  renderers=p_to_hover)
            p.add_tools(hover)
        try:
            # checks if 'right' is in aligment or not
            list(aligment.values()).index('right')
            p.add_layout(LinearAxis(y_range_name=self.y_right_name,
                                    axis_label=ylabel_right), 'right')
        except Exception as e:
            # warnings.warn(str(e))
            pass
        return p

    def build_dashboard(self,
                        input_data={},
                        aligment={},
                        params={},
                        title="stocks.py example",
                        ylabel='Price', ylabel_right={},
                        show=True,
                        column='adj_close',
                        height=[],
                        **kwargs_to_bokeh):
        plots = []
        _data, x_range, _names = Formatter().format_input_data(input_data,
                                                               column)
        _params = Formatter().format_params(_data, params, _names)
        _aligment = Formatter().format_aligment(aligment, _names)
        _y_label_right = Formatter().format_y_label_right(ylabel_right,
                                                          ylabel, _names)

        self.x_range = Range1d(x_range[0], x_range[-1])
        if not height:
            height = [(1. / len(_data))] * len(_data)
        else:
            assert len(height) == len(_data), (
                "Number of heights should be equal to the number of plots. " +
                "expected: %s, " % len(_data) +
                "found: %s, len(height)= %s. " % (height, len(height)))
            assert sum(height) == 1, (
                "All heights should sum up to 1, " +
                "found: %s, sum(height)=%s" % (height, sum(height)))
        for i, (plot_title, data) in enumerate(_data.items()):
            plots.append(self._plot_stock(
                data=data,
                names=_names[plot_title],
                title=plot_title,
                params=_params[plot_title],
                aligment=_aligment[plot_title],
                ylabel=ylabel,
                ylabel_right=_y_label_right[plot_title],
                height=height[i],
                ** kwargs_to_bokeh))

        layout = gridplot(plots,
                          plot_width=self.width,
                          ncols=self.ncols)
        self.layout = layout
        if show:
            curdoc().add_root(layout)
            curdoc().title = title
        return curdoc
