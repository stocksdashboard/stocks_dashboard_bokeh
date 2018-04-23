from __future__ import absolute_import

import pytest
from StocksDashboard import StocksDashboard as sdb


def test_init_variables_None():
    def ValueError_msg(varname):
        return "'%s cannot be None.'" % varname

    """with pytest.raises(ValueError) as excinfo:
                    sdb(width=None)
                assert str(excinfo.value) == ValueError_msg('width')

                with pytest.raises(ValueError) as excinfo:
                    sdb(height=None)
                assert str(excinfo.value) == ValueError_msg('height')

                with pytest.raises(ValueError) as excinfo:
                    sdb(ncols=None)
                assert str(excinfo.value) == ValueError_msg('ncols')"""

    # _args = [{'width': None}, {'height': None}, {'ncols': None}]
    _vars = ['width', 'height', 'ncols']
    for _varname in _vars:
        print(_varname)
        with pytest.raises(ValueError) as excinfo:
            sdb(**{_varname: None})
        assert str(excinfo.value) == ValueError_msg(_varname)


def test_init_variables_int():
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
