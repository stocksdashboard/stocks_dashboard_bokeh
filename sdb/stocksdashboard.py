import numpy as np
import pandas as pd
from bokeh.layouts import gridplot
from bokeh.plotting import figure
from bokeh.plotting import output_file
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
        ('value', '@y{0.000}')
    ]
    formatters = {
        '$x': 'datetime',
    }
    mode = 'vline'
    names = None

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

    @staticmethod
    def _get_x_y(data, column):
        """
            Get the x and y coordinates to be plotted in the line graph.

        Params
        ------
        data: pd.Series, pd.DataFrame, dict, sequence
            If dict: should contain the field 'date' in a datetime
            format to be plotted. If not a numerical ordinal sequence
            will be used.
        column: str
            Column or field from which select the timeseries. This is required
            for pd.Series, pd.DataFrame, dict formats.

        Returns
        -------
        x: sequence or array-like
            Sequence with dates or numbers corresponding to the timeseries
            steps.
        y: sequence or array-like
            Sequence with the time series to be plotted.

        """
        if isinstance(data, pd.Series):
            return data.copy(), data.copy()
        elif isinstance(data, (pd.DataFrame, dict)):
            if column in data:
                y = data[column]
            else:
                raise(ValueError("Selected column: '%s'" % column +
                                 " not in 'data' variable of type" +
                                 " %s." % type(data)))
            if 'date' in data:
                x = convert_to_datetime(data['date'])
            else:
                if hasattr(data, 'index'):
                    x = data.index
                else:
                    x = np.arange(len(y))
            return x, y
        else:
            y = data
            x = np.arange(len(y))
            return x, y

    @staticmethod
    def _update_params(params, kwargs={}, names=None):
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
            if not names or (names and not any([n in params for n in names])):
                params.update(kwargs)
            else:
                for n in names:
                    if n in params:
                        params[n].update(kwargs)
                    else:
                        params[n] = kwargs
            return params
        else:
            return kwargs

    @staticmethod
    def _add_color_and_legend(params, legend='', color='black'):
        _params = copy.deepcopy(params)
        if 'legend' not in _params:
            _params['legend'] = legend
        if 'color' not in _params:
            _params['color'] = color
        return _params

    def _get_params(self, params, name, color):
        """ Try to find specific parameters for a given name."""
        try:
            return self._add_color_and_legend(params[name], name, color)
        except (TypeError, KeyError):
            return self._add_color_and_legend(params, name, color)

    def _plot_stock(self, input_data=None, p=None, column='adj_close',
                    title="Stock Closing Prices", ylabel='Price',
                    add_hover=True, params={}, **kwargs_to_bokeh):

        if not p:
            p = figure(x_axis_type="datetime", title=title,
                       sizing_mode='scale_both')
            p.grid.grid_line_alpha = 0.3
            p.xaxis.axis_label = 'Date'
            p.yaxis.axis_label = ylabel

        data, names = Formatter().format_data(input_data)
        colors = get_colors(len(data))
        params = self._update_params(params=params, kwargs=kwargs_to_bokeh,
                                     names=names)
        p_to_hover = []
        for i, stock in enumerate(data):
            x, y = self._get_x_y(stock, column)
            _params = self._get_params(params, names[i], colors[i])
            _p = p.line(x, y, **_params)
            p_to_hover.append(_p)

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
        return p

    def build_dashboard(self,
                        input_data={},
                        params={},
                        title="stocks.py example",
                        ylabel='Price',
                        **kwargs_to_bokeh):
        plots = []
        _data = Formatter().format_input_data(input_data)
        _params = Formatter().format_params(input_data, params)

        for i, (plot_title, data) in enumerate(_data.items()):
            plots.append(self._plot_stock(input_data=data,
                                          title=plot_title,
                                          params=_params[plot_title],
                                          ylabel=ylabel,
                                          **kwargs_to_bokeh))

        layout = gridplot(plots,
                          plot_width=self.width,
                          plot_height=self.height,
                          ncols=self.ncols)
        curdoc().add_root(layout)
        curdoc().title = title
        return curdoc()


class Formatter():

    """
        Formats data to valid data accepted by StocksDashboard.

        Data should be contained in dicts, being the key of the dict the title
        of each plot element:
            - {'stocks': {'AAPL': AAPL, 'GOOG': GOOG,
                     'IBM': IBM, 'MSFT': MSFT, ...},
               'avg': {'AAPL_avg': aapl_avg, ...}}

        Each of the values of the input data dictionary
        should have either of the following formats:
            - dict of dicts:
                - must contains at least one ts column to be plotted
                  (set int :meth:StocksDashboard.build_dashboard()`:
                  {'GOOGL' : {'dates': ..., 'adj_close': ...}}
            - dict of pd.Series
                - index will be used as dates
            - dict of pandas.DataFrame:
                - index will be used as dates
                - data from `column` in StocksDashboard.plot_stock()
                  will be used.
            - dict of np.array
                - index will be a list of numbers
                - no column will be selected.
            - list of dicts with keys ('dates' and column):
                [{'dates': ..., 'adj_close': ...},
                 {'dates': ..., 'adj_close': ...}]
            - list of pd.Series / pd.DataFrame.
    """

    def __init__(self):
        self.name = None

    def _format(self, data):
        """
            Format data for plotting.
        """

        if isinstance(data, list):
            return self.__process_list(data)

        elif isinstance(data, dict):
            return self.__process_dict(data)

        elif isinstance(data, (pd.Series, pd.DataFrame, np.ndarray)):
            # Convert to a list of, at least,
            # one element, to be able to iterate.
            if not isinstance(data, pd.DataFrame):
                data = [pd.DataFrame(data)]
            else:
                data = [data]
        else:
            raise(TypeError("Data type is not valid."))

    @staticmethod
    def __is_valid_type(data):
        _valid_types = (pd.DataFrame, pd.Series, list, dict, np.ndarray)

        if not (data is None or isinstance(data, _valid_types)):

            raise(ValueError("Inappropiate value " +
                             "of 'data' : %s. " % data +
                             "Expected pandas.DataFrame, pandas.Series, " +
                             "or list of pandas objects."))
        return True

    def __process_list(self, data):
        """
            Format list to valid type.
        """
        # list of dictsxs
        if all([isinstance(d, dict) for d in data]):
            return [pd.DataFrame.from_dict(d) for d in data]
        # data is dict of pd.Series, pd.DataFrame or np.ndarray
        elif any([all([isinstance(d, data_type) for d in data])
                  for data_type in (pd.Series, pd.DataFrame, np.ndarray)]):
            return data
        else:
            raise(TypeError("Data is not valid. " +
                            "If 'list' elements should be:" +
                            " dicts, pd.Series or pd.DataFrame. " +
                            "Found : %s" % [type(d) for d in data]))

    def __process_dict(self, data):
        """
            Format dictionary to valid type.
        """
        self.names = list(data.keys())
        # dict of dicts
        if all([isinstance(d, dict) for k, d in data.items()]):
            result = {k: pd.DataFrame.from_dict(d) for k, d in data.items()}
            return list(result.values())
        # dict of dataframes, pd.Series or np.ndarray
        elif any([all([isinstance(d, data_type) for k, d in data.items()])
                  for data_type in (pd.Series, pd.DataFrame, np.ndarray)]):
            return list(data.values())
        else:
            raise(TypeError("Data not valid. Found dict containing objects" +
                            " of tpye %s." % [type(d) for d in data] +
                            "Please convert to format" +
                            " \{'name': \{'date': ..., 'values': ...\}\}"
                            "or {'name': {'date': pd.DataFrame}."))

    def format_data(self, data):
        """
            Check if data is a valid format and give required
            format if valid.
        """
        # Check data is valid type:
        # (pd.DataFrame, pd.Series, list, dict, np.ndarray)
        self.__is_valid_type(data)
        result = self._format(data)
        return result, self.names

    def format_input_data(self, input_data):
        assert isinstance(input_data, (dict, list)), (
            "Data should be contained in 'dict' object or 'list'")
        if isinstance(input_data, list):
            return {"plot_" + str(i): v for i, v in enumerate(input_data)}
        else:
            return input_data

    @staticmethod
    def _get_input_params(i, data, plot_title, params, data_dim):
        _params = {}
        if isinstance(params, dict):
            if plot_title in params:
                _params = copy.deepcopy(params[plot_title])
        elif isinstance(params, list):
            assert(data_dim == len(params)), "If input data contains " + \
                "a list, 'params' should contain a list of parameters" + \
                " for each element."
            _params = copy.deepcopy(params[i])
        return _params

    def format_params(self, input_data, params):
        if not isinstance(params, (dict, list)):
            raise(TypeError("'params' should be either 'dict' or 'list."))
        _params = {}
        _params = {plot_title: self._get_input_params(i, data, plot_title,
                                                      params, len(input_data))
                   for i, (plot_title, data) in enumerate(input_data.items())}
        return _params
