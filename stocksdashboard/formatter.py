#!/usr/bin/env python3
# Authors: Mabel Villalba Jimenez <mabelvj@gmail.com>,
#          Emilio Molina Martinez <emilio.mol.mar@gmail.com>
# License: GPLv3

import numpy as np
import pandas as pd
import copy


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

    def __reformat_x_list(self, data):
        # if all are pd.DataFrame or pd.Series -> merge indices!!
        if any([all([isinstance(d, data_type) for d in data])
                for data_type in (pd.Series, pd.DataFrame)]):
            # return each of the dataframes with the merged indices
            return [s.to_frame()
                    for c, s in pd.concat(copy.deepcopy(data),
                                          axis=1).iteritems()]

    def __reformat_x_dict(self, data):
        # if all are pd.DataFrame or pd.Series -> merge indices!!
        if any([all([isinstance(d, data_type) for k, d in list(data.items())])
                for data_type in (pd.Series, pd.DataFrame)]):
            # return each of the dataframes with the merged indices
            df_total = pd.concat(copy.deepcopy(data), axis=1)
            return {c: df_total.loc[:, c]
                    for c in set(df_total.columns.get_level_values(0))}

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
            result = self.__reformat_x_list(result)
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
        elif any([all([isinstance(d, data_type) for d in data])
                  for data_type in (pd.Series, pd.DataFrame)]):
            # Check all index are same type
            assert all([isinstance(d.index, type(data[0].index))
                        for d in data]), (
                "All indices in a list of pd.Series or pd.DataFrames " +
                "should have the same type.")
            result = self.__reformat_x_list(data)
            return result
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
        if all([isinstance(d, dict) for k, d in list(data.items())]):
            result = {k: pd.DataFrame.from_dict(
                d) for k, d in list(data.items())}
            # Has 'date' as a column -> format to common date
            if all(['date' in v for k, v in result.items()]):
                result = {k: df.set_index('date')
                          for k, df in list(result.items())}
            result = self.__reformat_x_dict(result)
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
        elif any([all([isinstance(d, data_type) for d in list(data.values())])
                  for data_type in (pd.Series, pd.DataFrame)]):
            assert all([isinstance(d.index, type(list(data.values())[0].index))
                        for d in list(data.values())]), (
                "All indices in a dict of pd.Series or pd.DataFrames " +
                "should have the same type.")
            result = self.__reformat_x_dict(data)
            return list(result.values())
        else:
            raise(TypeError("Data is not valid. " +
                            "Found dict containing objects" +
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
