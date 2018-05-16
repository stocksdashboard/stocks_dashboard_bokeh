#!/usr/bin/env python3
# Authors: Mabel Villalba Jimenez <mabelvj@gmail.com>,
#          Emilio Molina Martinez <emilio.mol.mar@gmail.com>
# License: GPLv3

import numpy as np
import pandas as pd
import copy
# try:
#     from .stocksdashboard import convert_to_datetime
# except Exception as excinfo:
#     print(str(excinfo))
#     from stocksdashboard import convert_to_datetime


def convert_to_datetime(x):
    return np.array(x, dtype=np.datetime64)


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

    def reformat_x_list(self, data):
        # if all are pd.DataFrame or pd.Series -> merge indices!!
        if any([isinstance(d, (pd.Series, pd.DataFrame)) for d in data]):
            # return each of the dataframes with the merged indices
            return [s.to_frame()
                    for c, s in pd.concat(copy.deepcopy(data),
                                          axis=1).iteritems()]

    def reformat_x_dict(self, data):
        # if all are pd.DataFrame or pd.Series -> merge indices!!
        if any([isinstance(d, (pd.Series, pd.DataFrame))
                for d in list(data.values())]):
            # return each of the dataframes with the merged indices
            df_total = pd.concat(copy.deepcopy(data), axis=1)
            columns = list(data.keys())
            return {c: df_total.loc[:, c] for c in columns}

    def __process_list(self, data):
        """
            Format list to valid type.
        """
        # list of dicts
        if all([isinstance(d, dict) for d in data]):
            result = [pd.DataFrame.from_dict(d) for d in data]
            # Has 'date' as a column -> format to common date
            if all(['date' in df for df in result]):
                result = [df.set_index('date') for df in result]
            n = len(result[0])
            # if not all([len(df) == n for df in result]):
            result = self.reformat_x_list(result)
            return result
        # data is list of np.ndarray
        elif all([isinstance(d, np.ndarray) for d in data]):
            result = data
            n = len(result[0])
            assert(all([len(arr) == n for arr in result])), (
                "All elements in a list of np.ndarray should have " +
                "the same length")
            return result
        # data is list of pd.Series, pd.DataFrame[
        elif any([isinstance(d, (pd.Series, pd.DataFrame)) for d in data]):
            # Check all index are same type
            assert all([isinstance(d.index, type(data[0].index))
                        for d in data]), (
                "All indices in a list of pd.Series or pd.DataFrames " +
                "should have the same type.")
            result = self.reformat_x_list(data)
            return result
        else:
            raise(TypeError("Data is not valid. " +
                            "If 'list' elements should be:" +
                            " dicts, pd.Series or pd.DataFrame. " +
                            "Found : %s" % [type(d) for d in data]))

    def __process_dict(self, _data):
        """
            Format dictionary to valid type.
        """
        data = copy.deepcopy(_data)
        self.names = list(data.keys())
        # dict of dicts
        if all([isinstance(d, dict) for d in list(data.values())]):
            result = {k: pd.DataFrame.from_dict(
                d) for k, d in list(data.items())}
            # Has 'date' as a column -> format to common date
            if all(['date' in v for k, v in result.items()]):
                result = {k: df.set_index('date')
                          for k, df in list(result.items())}
            result = self.reformat_x_dict(result)
            return list(result.values())
        # data is list of np.ndarray
        elif all([isinstance(d, np.ndarray) for d in list(data.values())]):
            result = data
            n = len(list(result.values())[0])
            assert(all([len(arr) == n for arr in list(result.values())])), (
                "All elements in a list of np.ndarray should have " +
                "the same length")
            return list(result.values())
        # dict of dataframes, pd.Series
        elif any([isinstance(d, (pd.Series, pd.DataFrame))
                  for d in list(data.values())]):
            assert all([isinstance(d.index, type(list(data.values())[0].index))
                        for d in list(data.values())]), (
                "All indices in a dict of pd.Series or pd.DataFrames " +
                "should have the same type.")

            result = self.reformat_x_dict(data)
            return list(result.values())
        else:
            raise(TypeError("Data is not valid. " +
                            "Found dict containing objects" +
                            " of tpye %s." % [type(d) for d in list(data)] +
                            "Please convert to format" +
                            " \{'name': \{'date': ..., 'values': ...\}\}"
                            "or {'name': {'date': pd.DataFrame}."))

    @staticmethod
    def _get_x_y(data, column=None):
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
            return data.index.copy(), data.copy()
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

    def format_input_data(self, input_data, column='adj_close'):
        assert isinstance(input_data, (dict, list)), (
            "Data should be contained in 'dict' object or 'list'")
        if isinstance(input_data, list):
            result = {"plot_" + str(i): v for i, v in enumerate(input_data)}
        else:
            result = input_data

        names = {}
        dict_total = {}
        _temp = {}
        for j, (plot_title, data) in enumerate(result.items()):
            _temp[plot_title], names[plot_title] = self.format_data(data)
            dict_total[plot_title] = {}
            for i, stock in enumerate(_temp[plot_title]):
                _, y = self._get_x_y(stock, column)
                dict_total[plot_title][names[plot_title][i]] = y
        df_total = {k: pd.concat(l, axis=1)
                    for k, l in list(dict_total.items())}
        # it's in __process_dict
        x_range = pd.concat(copy.deepcopy(df_total), axis=1).index
        formatted_data = self.__process_dict(df_total)

        formatted_result = {}
        for j, (plot_title, v) in enumerate(list(names.items())):
            _temp = {}
            for i, name in enumerate(v):
                _temp[name] = formatted_data[j][name]
            formatted_result[plot_title] = list(_temp.values())
        return formatted_result, x_range, names

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

    def format_params(self, input_data, params, names):
        if not isinstance(params, (dict, list)):
            raise(TypeError("'params' should be either 'dict' or 'list."))
        _params = {}
        _params = {plot_title: self._get_input_params(
            i,
            input_data[plot_title],
            plot_title,
            params, len(input_data))
            for i, (plot_title, stocksnames) in enumerate(names.items())}
        return _params

    def format_aligment(self, aligment, names):
        """
            Reviews input aligment setting to match the available 'names'
            structure and in case there is no parameter, set the
            stock to be at the left.
        """
        if not isinstance(aligment, (dict)):
            raise(TypeError("'aligment' should be either 'dict' in the form" +
                            "\{plot_title : \{stockname: 'left', ...\}\}"))
        for plot_title, _names in list(names.items()):
            if plot_title not in aligment:
                aligment[plot_title] = {}
            for stockname in _names:
                try:
                    if (not aligment[plot_title][stockname] or
                        not aligment[plot_title][stockname]
                            in ('left', 'right', None)):
                        aligment[plot_title][stockname] = None
                except:
                    aligment[plot_title][stockname] = None
            # remove keys that are not present in data
            for alig_name in list(aligment[plot_title].keys()):
                if alig_name not in _names:
                    del(aligment[plot_title][alig_name])
        # Order the dict to match the order in 'names'.
        # The order in dictionary elements corresponds to the order
        # of adding the element.
        result = {}
        for plot_title, _names in list(names.items()):
            result[plot_title] = {}
            for stockname in _names:
                result[plot_title][stockname] = aligment[plot_title][stockname]
        return result

    def format_y_label_right(self, y_label_right, y_label, names):
        if not isinstance(y_label_right, (dict)):
            raise(TypeError("'ylabel_right' should be either 'dict'" +
                            " in the form {plot_title : y_label_right}"))
        for plot_title in list(names.keys()):
            # if there is only one element in the plot (plot_title)
            # and there is no label for it, copy left y_label
            # in case there is need to alight to the right
            if len(names[plot_title]) == 1:
                y_label_right[plot_title] = y_label
            elif plot_title not in y_label_right:
                y_label_right[plot_title] = None
        return y_label_right
