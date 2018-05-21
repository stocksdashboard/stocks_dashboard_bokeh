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
import datetime

from bokeh.layouts import gridplot
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.models import Range1d
from bokeh.models.ranges import DataRange1d

from bokeh.models import LinearAxis
from bokeh.models import Axis
from bokeh.models.glyphs import Line
from bokeh.core.properties import value
import warnings
import copy

from bokeh.models import HoverTool
from bokeh.io import curdoc
from bokeh.layouts import row, widgetbox
import bokeh

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
                >>> sdb._update_params(params = {'line_style': 'dot',
                ...                             'color': 'blue'},
                ...                   kwargs = {'line_width': 1.5})
                {'color': 'blue', 'line_style': 'dot', 'line_width': 1.5}
            If params contains names:
                - Update each dict:
                >>> sdb._update_params(params = {
                ... 'GOOGL': {'line_style': 'dot'}, 'AAPL' :{'color': 'blue'}},
                ...                   kwargs = {'line_width': 1.5},
                ...                   names = ['GOOGL', 'AAPL'])
                {'AAPL': {'color': 'blue', 'line_width': 1.5},
                'GOOGL': {'line_style': 'dot', 'line_width': 1.5}}
            If both ``params`` and ``kwargs`` are empty, ``kwargs``
            is returned.
                >>> sdb._update_params(params = {}, kwargs={})
                {}
        """
        if params or kwargs:
            if (not names or
                (names and not any([n in params for n in names]) and not
                    aligment)):
                params.update(copy.deepcopy(kwargs))
            else:
                # Params has parameters but not especific params per name.
                _initial_params = copy.deepcopy(kwargs)
                if params and not all([n in params for n in names]):
                    # delete global formatting from params
                    for k, v in list(params.items()):
                        if k not in names:
                            # Override kwargs with params for the plot
                            _initial_params.update(copy.deepcopy({k: v}))
                            del(params[k])
                for i, n in enumerate(names):
                    temp_params = copy.deepcopy(_initial_params)
                    # Particular parameters override general ones
                    if n in params:
                        temp_params.update(params[n])
                    params[n] = copy.deepcopy(temp_params)

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
    def _add_color_and_legend(params, legend=False, color='black'):
        _params = copy.deepcopy(params)
        if 'legend' not in _params:
            _params['legend'] = value(legend)
        elif isinstance(_params['legend'], str):
            _params['legend'] = value(copy.deepcopy(_params['legend']))
        if 'color' not in _params:
            _params['color'] = color
        return _params

    @staticmethod
    def __get_class_attr(params, class_object):
        if not isinstance(class_object, (list, tuple)):
            class_object = [class_object]
        # return {k: v for k, v in list(copy.deepcopy(params).items())
        #         if any([hasattr(c, k) for c in class_object])}
        result = {}
        for k, v in list(params.items()):
            if any([hasattr(c, k) for c in class_object]):
                result[k] = v
        return result

    def __get_kwargs_to_figure(self, _params):
        """
            From the input parameter for the current plot,
            select the ones that are properties of Figure
            and remove them from 'params' so the rest available
            are just params for Line.
        """
        params = copy.deepcopy(_params)
        kwargs_to_figure = self.__get_class_attr(params,
                                                 bokeh.plotting.figure())
        for k, v in list(kwargs_to_figure.items()):
            del(params[k])
        # bokeh.plotting.figure(**kwargs) creates a Figure
        # with the **kwargs but if not present,
        # the aethetics are not passed to the FigureOptions class
        # and hence they do not appear as element of the class.
        # https://bokeh.pydata.org/en/latest/_modules/bokeh/plotting/figure.html#Figure
        for k, v in list(params.items()):
            try:
                bokeh.plotting.figure(**{k: v})
                kwargs_to_figure[k] = copy.deepcopy(v)
                del(params[k])
            except Exception as excinfo:
                # print(str(excinfo))
                pass
        return kwargs_to_figure, params

    def __get_ranges(self, kwargs_to_figure, keyword='extra_y_ranges'):
        if keyword in kwargs_to_figure:
            value = kwargs_to_figure[keyword]
            del[kwargs_to_figure[keyword]]
        else:
            if hasattr(self, keyword):
                value = getattr(self, keyword)
            else:
                value = None
        return kwargs_to_figure, value

    def _get_params(self, params, name, color,
                    class_object=[bokeh.models.glyphs.Line,
                                  bokeh.core.property_mixins.ScalarLineProps]):
        """ Try to find specific parameters for a given name."""
        try:
            _params = self._add_color_and_legend(params[name], name, color)
        except (TypeError, KeyError):
            _params = self._add_color_and_legend(params, name, color)
        return _params

    def __update_datasource(self, datasource, stock, column, name):
        """
            Update the object datasource with data from each stock.
        """
        x, y = Formatter._get_x_y(stock, column)
        datasource.add(name=name, data=y)
        if 'x' not in datasource.data:
            datasource.add(name='x', data=x)
        return datasource

    def get_y_limits(self, data, aligment, position='right', x_range=None):
        ix_range = pd.date_range(x_range.start, x_range.end)
        _min = None
        _max = None
        for i, (stockname, al) in enumerate(list(aligment.items())):
            if al == position:
                _data = data[i][ix_range]
                if _min:
                    _min = min(_min, np.nanmin(_data))
                else:
                    _min = np.nanmin(_data)
                if _max:
                    _max = max(_max, np.nanmax(_data))
                else:
                    _max = np.nanmax(_data)
        return _min, _max

    def set_limits(self, p, data, aligment, extra_y_ranges=None,
                   x_range=None, y_range_in_params=False):
        try:
            # checks if 'right' is in aligment or not
            list(aligment.values()).index('right')
            if len(data) == 1:
                # There is only one element
                # and we want to align it to the right
                p.yaxis.visible = False
            self.y_right_name = 'y1'
            if not extra_y_ranges:
                y_limits_right = self.get_y_limits(data, aligment, 'right',
                                                   x_range)
                p.extra_y_ranges = {self.y_right_name:
                                    Range1d(y_limits_right[0],
                                            y_limits_right[1])}
            else:
                p.extra_y_ranges = {
                    self.y_right_name: extra_y_ranges}
        except Exception as excinfo:
            # print(str(excinfo))
            pass

        if not y_range_in_params:
            # make sure that left limits are set to only signals in the left.
            y_limits_left = self.get_y_limits(data, aligment, 'left', x_range)
            try:
                p.yaxis.y_range = Range1d(y_limits_left[0], y_limits_left[1])
            except Exception as excinfo:
                # print(str(excinfo))
                pass
        return p

    def separate_Figure_and_Line_params(self, params, kwargs_to_bokeh):
        # Extract Figure attr from global settings dict kwargs_to_bokeh
        (kwargs_to_figure_general,
            kwargs_to_bokeh) = self.__get_kwargs_to_figure(kwargs_to_bokeh)

        # Extract Figure attr from the particular params for the plot.
        (kwargs_to_figure,
            params) = self.__get_kwargs_to_figure(params)

        # Extract right limits in case there are limits for the right plot
        (kwargs_to_figure,
         extra_y_ranges) = self.__get_ranges(kwargs_to_figure,
                                             'extra_y_ranges')
        kwargs_to_figure_general.update(kwargs_to_figure)
        _kwargs_to_figure = copy.deepcopy(kwargs_to_figure_general)

        return params, kwargs_to_bokeh, _kwargs_to_figure, extra_y_ranges

    def _plot_stock(self, data=None, names=None, p=None, column='adj_close',
                    title="Stock Closing Prices",
                    ylabel_right=None, add_hover=True,
                    params={}, aligment={}, height=None,
                    verbose=False, **kwargs_to_bokeh):
        if not p:
            (params,
             kwargs_to_bokeh,
             kwargs_to_figure,
             extra_y_ranges) = self.separate_Figure_and_Line_params(
                params, kwargs_to_bokeh)
            p = figure(x_axis_type="datetime", title=title,
                       sizing_mode='scale_both', plot_width=self.width,
                       **kwargs_to_figure)
            if height:
                p.plot_height = int(height * self.height)
                # print(int(height*self.height))
            p.grid.grid_line_alpha = 0.3
            p.xaxis.axis_label = 'Date'
            p = self.set_limits(
                p, data, aligment, extra_y_ranges, kwargs_to_figure['x_range'],
                y_range_in_params=('y_range' in kwargs_to_figure))

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
            if verbose:
                print(names[i], _params)
            _p = p.line(x='x', y=names[i], source=__datasource, **_params)
            p_to_hover.append(_p)

        assert(len(__datasource.data) == len(data) + 1), (
            "Number of elements used as source don't match " +
            "data dimension.")  # len(data) + 1 -> all data and the x-axis
        self.datasources.append(__datasource)

        assert(len(p_to_hover) == len(data)), "Number of Lines " + \
                                              "don't match data dimension."
        # p.legend.orientation = "horizontal"
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
        kwargs_to_bokeh['y_axis_label'] = ylabel
        if 'x_range' not in kwargs_to_bokeh:
            kwargs_to_bokeh['x_range'] = Range1d(x_range[0], x_range[-1])
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
