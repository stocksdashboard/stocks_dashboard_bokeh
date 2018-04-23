from __future__ import absolute_import

import pytest
from stocks_dashboard_bokeh.stocksdashboard import StocksDashboard as sdb


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
