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
    widgets = None
    sliders = None

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
        self.check_variables()

    def check_variables(self, varname=None):

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
    def create_hover(tooltips=[('date', '$x{%F}'), ('value', '@y{0.000}')],
                     formatters={'$x': 'datetime'}, mode='vline', **kwargs):
        hover = HoverTool(**kwargs)
        hover.tooltips = tooltips
        hover.formatters = formatters
        hover.mode = mode
        return hover

    @property
    def names(self):
        return self._names

    @names.setter
    def names(self, names):
        assert(isinstance(names, list)), "'names' should be a list."
        if not hasattr(self, '_names') or not self._names:
            # If empty, create a list.
            self._names = [names]
        else:
            # Add to the list of elements
            self._names.append([names])

    def retrieve_names(self, data):
        if self.names and len(self.names[-1]) == len(data):
            names = self.names[-1]
        else:
            names = np.arange(len(data))
        return names

    def check_valid(self, df):
        """
            Check that the dataframes for plotting are the valid type.
        """
        if not (df is None or isinstance(df,
                                         (pd.DataFrame, pd.Series,
                                          list, dict, np.ndarray))):

            raise(ValueError("Inapropiate value of df: %s." % df +
                             "Expected pandas.DataFrame, pandas.Series, " +
                             "or list of pandas objects"""))

        if isinstance(df, list):
            if all([isinstance(d, dict) for d in df]):
                return [pd.DataFrame.from_dict(d)
                        if not isinstance(d.values(), dict)
                        else StocksDashboard.check_valid(d)
                        for d in df]
            else:
                return StocksDashboard.check_valid(df[0])
        if isinstance(df, dict):
            if all([isinstance(d, dict) for k, d in df.items()
                    if hasattr(d, 'values')]):
                result = {k: pd.DataFrame.from_dict(d) for k, d in df.items()
                          if hasattr(d, 'values')}
                self.names = list(result.keys())
                return list(result.values())
            elif all([isinstance(d, pd.DataFrame) for k, d in df.items()
                      if hasattr(d, 'values')]):
                self.names = list(df.keys())
                return list(df.values())
            else:
                raise(ValueError("Dict containing objects" +
                                 " of tpye %s." % type(df) +
                                 "Please convert to format" +
                                 " \{'name': \{'date': ..., 'values': ...\}\}"
                                 "or {'name': {'date': pd.DataFrame}."))
        return True

    def check_datasource(self, df, inplace=False):
        # Check df is pandas or list of pandas

        result = self.check_valid(df)

        if not isinstance(result, bool):
            df = result

        if not isinstance(df, (list, dict)):
            # Convert to a list of, at least,
            # one element, to be able to iterate.
            if not isinstance(df, pd.DataFrame):
                df = [pd.DataFrame(df)]
            else:
                df = [df]
        return copy.deepcopy(df)

    @staticmethod
    def get_x_y(data, column):
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
        if (isinstance(data, (pd.Series, pd.DataFrame, dict))):
            if isinstance(data, pd.Series):
                y = data.copy()
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
        else:
            y = data
            x = np.arange(len(y))
        return x, y

    def plot_stock(self, input_data=None, p=None, column='adj_close',
                   title="Stock Closing Prices", ylabel='Price',
                   add_hover=True, **kwargs):

        if not p:
            p = figure(x_axis_type="datetime", title=title,
                       sizing_mode='scale_both')
            p.grid.grid_line_alpha = 0.3
            p.xaxis.axis_label = 'Date'
            p.yaxis.axis_label = ylabel

        data = self.check_datasource(input_data)
        colors = get_colors(len(data))

        names = self.retrieve_names(data)

        p_to_hover = []
        for i, stock in enumerate(data):
            x, y = self.get_x_y(stock, column)
            __p = p.line(x, y, color=colors[i],
                         legend=names[i], **kwargs)  # _df.name
            p_to_hover.append(__p)

        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        if add_hover:
            hover = StocksDashboard.create_hover(self.tooltips,
                                                 self.formatters,
                                                 self.mode,
                                                 renderers=p_to_hover)
            p.add_tools(hover)
        return p

    @staticmethod
    def get_plots_params(**kwargs):
        if isinstance(kwargs, list):
            params1 = kwargs[0]
            if len(kwargs) == 2:
                params2 = kwargs[1]
            elif len(kwargs) == 1:
                params2 = params1
            else:
                raise(ValueError("If list of paramenters passed per plot," +
                                 "the maximum number of list is 2."))
        else:
            params1 = kwargs
            params2 = kwargs
        return params1, params2

    def build_dashboard(self, data1=None, data2=None,
                        title="stocks.py example",
                        output_filename="stocks", **kwargs):

        params1, params2 = StocksDashboard.get_plots_params(**kwargs)

        p1 = self.plot_stock(input_data=data1, **params1)
        p2 = self.plot_stock(input_data=data2, **params2)

        # open a browser
        layout = gridplot([p1, p2],
                          plot_width=self.width, plot_height=self.height,
                          ncols=self.ncols)

        # show(layout)
        if self.widgets:
            inputs = widgetbox(self.sliders.values())
            # for w in self.sliders.values():
            #     # print(w)
            #     w.on_change('value',
            # self.on_development().build_dashboard().update_data)

            curdoc().add_root(row(inputs, layout, width=self.width))
        else:
            curdoc().add_root(layout)
        curdoc().title = title
        output_file("%s.html" % output_filename, title=title)
        return curdoc()
