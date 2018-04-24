from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytest
from sdb import StocksDashboard as sdb
from sdb import Formatter

import numpy as np

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


def test_init_formatter_type():
    _sdb = sdb().build_dashboard(data1=data1, data2=data2)
    with pytest.raises(ValueError) as excinfo:
        Formatter(_sdb)
    assert ("'sdb' should be of class 'StocksDashboard'." +
            "Found class %s" % type(_sdb) in str(excinfo))
