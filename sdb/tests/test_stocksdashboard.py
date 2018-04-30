from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytest
from sdb import StocksDashboard as sdb
from sdb import Formatter

import numpy as np
import pandas as pd
import random
import string
import copy


low = 0
high = 100
size = 50
np.random.seed(42)

data1 = {'A': np.random.uniform(low=low, high=high, size=(size,)),
         'B': np.random.uniform(low=low, high=high, size=(size,)),
         'C': np.random.uniform(low=low, high=high, size=(size,))}

data2 = {'X': np.random.uniform(low=low, high=high, size=(size,)),
         'Y': np.random.uniform(low=low, high=high, size=(size,)),
         'Z': np.random.uniform(low=low, high=high, size=(size,))}


def error_checker(f, error, error_msg):
    with pytest.raises(error) as excinfo:
        eval(f)
    assert(error_msg in str(excinfo))


def test_init_variables_None():
    """
        Test that __init__ variables when set to None
        raise the proper error.
    """
    def ValueError_msg(varname):
        return "'%s cannot be None.'" % varname

    _vars = ['width', 'height', 'ncols']
    for _varname in _vars:
        print(_varname)
        with pytest.raises(ValueError) as excinfo:
            sdb(**{_varname: None})
        assert str(excinfo.value) == ValueError_msg(_varname)


def test_init_variables_not_int():
    """
        Test that __init__ values not int raise adequate errors.
    """
    def TypeError_msg(varname, value):
        msg = "'%s cannot be of" % varname + \
              "type %s, must be 'int'" % type(value)
        return msg

    _vars = ['width', 'height', 'ncols']
    _test_values = [10., 'a']
    for _test_value in _test_values:
        for _varname in _vars:
            with pytest.raises(TypeError) as excinfo:
                sdb(**{_varname: _test_value})
            assert str(excinfo.value) == TypeError_msg(_varname, _test_value)


def test_init_variables_int():
    """
        Test that __init__ values int raise error.
    """
    def TypeError_msg(varname, value):
        msg = "'%s cannot be of" % varname + \
              "type %s, must be 'int'" % type(value)
        return msg

    _vars = ['width', 'height', 'ncols']
    _test_values = [10]
    for _test_value in _test_values:
        for _varname in _vars:
            sdb(**{_varname: _test_value})


def test_init_unexpected_attribute():
    with pytest.raises(TypeError) as excinfo:
        sdb(span=10)
    assert ("__init__() got an unexpected keyword argument 'span'"
            in str(excinfo))


def test_update_params():
    # Test combine params with kwargs
    expected = {'color': 'blue', 'line_style': 'dot', 'line_width': 1.5}
    result = sdb._update_params(params={'line_style': 'dot',
                                        'color': 'blue'},
                                kwargs={'line_width': 1.5})
    assert result == expected

    # Test combine params with kwargs for different names.
    expected = {'AAPL': {'color': 'blue', 'line_width': 1.5},
                'GOOGL': {'line_style': 'dot', 'line_width': 1.5}}
    result = sdb._update_params(params={'GOOGL': {'line_style': 'dot'},
                                        'AAPL': {'color': 'blue'}},
                                kwargs={'line_width': 1.5},
                                names=['GOOGL', 'AAPL'])
    assert result == expected


def test_add_color_and_legend_legend():
    expected = {'color': 'black', 'legend': 'ABC'}
    result = sdb._add_color_and_legend({}, legend='ABC')
    assert result == expected

    expected = {'color': 'black', 'legend': 'A'}
    result = sdb._add_color_and_legend({'legend': 'A'}, legend='ABC')
    assert result == expected


def test_add_color_and_legend_color():
    expected = {'color': 'blue', 'legend': ''}
    result = sdb._add_color_and_legend({}, color='blue')
    assert result == expected

    expected = {'color': 'red', 'legend': ''}
    result = sdb._add_color_and_legend({'color': 'red'}, color='blue')
    assert result == expected

# Test Formatter()


def test_formatter_format_data_invalid_type():
    data = 10
    with pytest.raises(ValueError) as excinfo:
        Formatter().format_data(data)
    error_msg = "Inappropiate value of 'data' : %s. " % data + \
                "Expected pandas.DataFrame, pandas.Series, " + \
                "or list of pandas objects."
    assert(error_msg in str(excinfo))


def test_formatter_format_invalid_type():
    data = 10
    with pytest.raises(TypeError) as excinfo:
        Formatter()._format(data)
    error_msg = "Data type is not valid."
    assert(error_msg in str(excinfo))


def test_formatter_format_list():
    # Check list of pd.DataFrame is valid
    data = [pd.DataFrame(np.random.uniform(low=low, high=high, size=(size,)))
            for i in range(3)]
    assert Formatter()._format(data) == data

    # Check list of pd.Series is valid
    data = [pd.Series(np.random.uniform(low=low, high=high, size=(size,)))
            for i in range(3)]
    assert Formatter()._format(data) == data

    # Check list of numpy.array is valid
    data = [np.random.uniform(low=low, high=high, size=(size,))
            for i in range(3)]
    assert Formatter()._format(data) == data

    # Check list of strings is invalid
    data = [[random.choice(string.ascii_letters) for j in range(size)]
            for i in range(3)]
    with pytest.raises(TypeError) as excinfo:
        Formatter()._format(data)
    error_msg = "Data is not valid. " + \
                "If 'list' elements should be:" + \
                " dicts, pd.Series or pd.DataFrame."
    assert(error_msg in str(excinfo))


def test_formatter_format_dict():

    # Check dict of dicts is valid
    data = {str(i): {'col_' + str(j): np.random.uniform(low=low,
                                                        high=high,
                                                        size=(size,))
                     for j in range(3)}
            for i in range(3)}
    result = Formatter()._format(data)
    expected = list({k: pd.DataFrame.from_dict(d)
                     for k, d in data.items()}.values())
    assert all([r.equals(e) for r, e in zip(result, expected)])

    # Check dict of pd.DataFrame is valid
    data = {str(i): pd.DataFrame(np.random.uniform(low=low, high=high,
                                                   size=(size,)))
            for i in range(3)}
    assert Formatter()._format(data) == list(data.values())

    # Check dict of pd.Series is valid
    data = {str(i): pd.Series(np.random.uniform(low=low, high=high,
                                                size=(size,)))
            for i in range(3)}
    assert Formatter()._format(data) == list(data.values())

    # Check dict of numpy.array is valid
    data = {str(i): np.random.uniform(low=low, high=high, size=(size,))
            for i in range(3)}
    print(Formatter()._format(data))
    assert Formatter()._format(data) == list(data.values())

    # Check dict of strings is invalid
    data = {str(i): [random.choice(string.ascii_letters) for j in range(size)]
            for i in range(3)}
    with pytest.raises(TypeError) as excinfo:
        Formatter()._format(data)
    error_msg = "Data not valid. Found dict containing objects"
    assert(error_msg in str(excinfo))


def test_formatter_format_dict_names():
    # Check dict of dicts is valid
    data = {str(i): {'col_' + str(j): np.random.uniform(low=low,
                                                        high=high,
                                                        size=(size,))
                     for j in range(3)}
            for i in range(3)}
    f = Formatter()
    f._format(data)
    assert f.names == list(data.keys())

    # Check dict of pd.DataFrame is valid
    data = {str(i): pd.DataFrame(np.random.uniform(low=low, high=high,
                                                   size=(size,)))
            for i in range(3)}
    f = Formatter()
    f._format(data)
    assert f.names == list(data.keys())

    # Check dict of pd.Series is valid
    data = {str(i): pd.Series(np.random.uniform(low=low, high=high,
                                                size=(size,)))
            for i in range(3)}
    f = Formatter()
    f._format(data)
    assert f.names == list(data.keys())

    # Check dict of numpy.array is valid
    data = {str(i): np.random.uniform(low=low, high=high, size=(size,))
            for i in range(3)}
    f = Formatter()
    f._format(data)
    assert f.names == list(data.keys())

    # Check dict of strings is invalid
    data = {str(i): [random.choice(string.ascii_letters) for j in range(size)]
            for i in range(3)}
    with pytest.raises(TypeError) as excinfo:
        Formatter()._format(data)
    error_msg = "Data not valid. Found dict containing objects"
    assert(error_msg in str(excinfo))


def test_formatter_format_input_data():
    # Test dict of dicts
    data = {'plot_' + str(h): {str(i): {'col_' + str(j):
                                        np.random.uniform(low=low,
                                                          high=high,
                                                          size=(size,))
                                        for j in range(3)}
                               for i in range(3)}
            for h in range(2)}
    expected = data
    result = Formatter().format_input_data(data)
    assert result == expected

    # Test list of dicts
    data = [{str(i): {'col_' + str(j): np.random.uniform(low=low,
                                                         high=high,
                                                         size=(size,))
                      for j in range(3)}
             }
            for i in range(3)]
    expected = {"plot_" + str(i): v for i, v in enumerate(data)}
    result = Formatter().format_input_data(data)
    assert result == expected


def test_formatter_format_param_dict():
    # Test passing input params
    # (as passed to StocksDashboard().build_dashboard()) in dict format.

    data = {'plot_' + str(h): {str(i): {'col_' + str(j):
                                        np.random.uniform(low=low,
                                                          high=high,
                                                          size=(size,))
                                        for j in range(3)}
                               for i in range(3)}
            for h in range(2)}

    _data = Formatter().format_input_data(data)

    # Test dicts of params with one setting per graph.
    params = {'plot_' + str(h): {str(i): {'col_' + str(j):
                                          {'line_dash': 'dashed'}
                                          for j in range(3)}
                                 for i in range(3)}
              for h in range(2)}

    expected = {plot_title: copy.deepcopy(params[plot_title])
                for i, (plot_title, data) in enumerate(_data.items())}
    result = Formatter().format_params(_data, params)
    assert result == expected

    # Test dicts where not all 'plots_' have params params.
    params = {'plot_' + str(h): {str(i): {'col_' + str(j):
                                          {'line_dash': 'dashed'}
                                          for j in range(3)}
                                 for i in range(3)}
              for h in range(1)}

    expected = {plot_title: copy.deepcopy(params[plot_title])
                if plot_title in params else {}
                for i, (plot_title, data) in enumerate(_data.items())}
    result = Formatter().format_params(_data, params)
    assert result == expected


def test_formatter_format_param_list():
    # Test passing input params
    # (as passed to StocksDashboard().build_dashboard()) in list format.
    data = {'plot_' + str(h): {str(i): {'col_' + str(j):
                                        np.random.uniform(low=low,
                                                          high=high,
                                                          size=(size,))
                                        for j in range(3)}
                               for i in range(3)}
            for h in range(2)}

    _data = Formatter().format_input_data(data)

    # Test list of params with one setting per graph.
    params = [{str(i): {'col_' + str(j):
                        {'line_dash': 'dashed'}
                        for j in range(3)}
               for i in range(3)}
              for h in range(2)]

    expected = {plot_title: copy.deepcopy(params[i])
                for i, (plot_title, data) in enumerate(_data.items())}
    result = Formatter().format_params(_data, params)
    assert result == expected

    # Test list of params with less format elements than
    # elements in the plots. Should raise an error since if list
    # all elements should contain a formatting.
    params = [{str(i): {'col_' + str(j):
                        {'line_dash': 'dashed'}
                        for j in range(3)}
               for i in range(3)}
              for h in range(1)]  # 1 element vs 2 in data.
    print(params)
    with pytest.raises(AssertionError) as excinfo:
        Formatter().format_params(_data, params)
    msg = "If input data contains a list, 'params' should contain " + \
          "a list of parameters for each element."
    assert(msg in str(excinfo))
