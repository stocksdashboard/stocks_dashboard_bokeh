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

# Test Formatter()


def test_formatter_check_valid_invalid_type():
    data = 10
    with pytest.raises(ValueError) as excinfo:
        Formatter().check_valid(data)
    error_msg = "Inappropiate value of 'data' : %s. " % data + \
                "Expected pandas.DataFrame, pandas.Series, " + \
                "or list of pandas objects."
    assert(error_msg in str(excinfo))


def test_formatter_check_valid_list():
    # Check list of pd.DataFrame is valid
    data = [pd.DataFrame(np.random.uniform(low=low, high=high, size=(size,)))
            for i in range(3)]
    assert Formatter().check_valid(data) == data

    # Check list of pd.Series is valid
    data = [pd.Series(np.random.uniform(low=low, high=high, size=(size,)))
            for i in range(3)]
    assert Formatter().check_valid(data) == data

    # Check list of numpy.array is valid
    data = [np.random.uniform(low=low, high=high, size=(size,))
            for i in range(3)]
    assert Formatter().check_valid(data) == data

    # Check list of strings is invalid
    data = [[random.choice(string.ascii_letters) for j in range(size)]
            for i in range(3)]
    with pytest.raises(TypeError) as excinfo:
        Formatter().check_valid(data)
    error_msg = "Data is not valid. " + \
                "If 'list' elements should be:" + \
                " dicts, pd.Series or pd.DataFrame."
    assert(error_msg in str(excinfo))


def test_formatter_check_valid_dict():

    # Check dict of dicts is valid
    data = {str(i): {'col_' + str(j): np.random.uniform(low=low,
                                                        high=high,
                                                        size=(size,))
                     for j in range(3)}
            for i in range(3)}
    result = Formatter().check_valid(data)
    expected = list({k: pd.DataFrame.from_dict(d)
                     for k, d in data.items()}.values())
    assert all([r.equals(e) for r, e in zip(result, expected)])

    # Check dict of pd.DataFrame is valid
    data = {str(i): pd.DataFrame(np.random.uniform(low=low, high=high,
                                                   size=(size,)))
            for i in range(3)}
    assert Formatter().check_valid(data) == list(data.values())

    # Check dict of pd.Series is valid
    data = {str(i): pd.Series(np.random.uniform(low=low, high=high,
                                                size=(size,)))
            for i in range(3)}
    assert Formatter().check_valid(data) == list(data.values())

    # Check dict of numpy.array is valid
    data = {str(i): np.random.uniform(low=low, high=high, size=(size,))
            for i in range(3)}
    print(Formatter().check_valid(data))
    assert Formatter().check_valid(data) == list(data.values())

    # Check dict of strings is invalid
    data = {str(i): [random.choice(string.ascii_letters) for j in range(size)]
            for i in range(3)}
    with pytest.raises(TypeError) as excinfo:
        Formatter().check_valid(data)
    error_msg = "Data not valid. Found dict containing objects"
    assert(error_msg in str(excinfo))


def test_formatter_check_valid_dict_names():
    # Check dict of dicts is valid
    data = {str(i): {'col_' + str(j): np.random.uniform(low=low,
                                                        high=high,
                                                        size=(size,))
                     for j in range(3)}
            for i in range(3)}
    f = Formatter()
    f.check_valid(data)
    assert f.names == list(data.keys())

    # Check dict of pd.DataFrame is valid
    data = {str(i): pd.DataFrame(np.random.uniform(low=low, high=high,
                                                   size=(size,)))
            for i in range(3)}
    f = Formatter()
    f.check_valid(data)
    assert f.names == list(data.keys())

    # Check dict of pd.Series is valid
    data = {str(i): pd.Series(np.random.uniform(low=low, high=high,
                                                size=(size,)))
            for i in range(3)}
    f = Formatter()
    f.check_valid(data)
    assert f.names == list(data.keys())

    # Check dict of numpy.array is valid
    data = {str(i): np.random.uniform(low=low, high=high, size=(size,))
            for i in range(3)}
    f = Formatter()
    f.check_valid(data)
    assert f.names == list(data.keys())

    # Check dict of strings is invalid
    data = {str(i): [random.choice(string.ascii_letters) for j in range(size)]
            for i in range(3)}
    with pytest.raises(TypeError) as excinfo:
        Formatter().check_valid(data)
    error_msg = "Data not valid. Found dict containing objects"
    assert(error_msg in str(excinfo))
