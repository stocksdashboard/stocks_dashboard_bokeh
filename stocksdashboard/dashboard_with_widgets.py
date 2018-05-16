#!/usr/bin/env python3
# Authors: Mabel Villalba Jimenez <mabelvj@gmail.com>,
#          Emilio Molina Martinez <emilio.mol.mar@gmail.com>
# License: GPLv3

# Multiple formats for each line.
from bokeh.models.widgets import Slider
from bokeh.models.widgets import PreText

import re
import copy
import pandas as pd
import numpy as np

try:
    from ..stocksdashboard.stocksdashboard import StocksDashboard
except Exception as excinfo:
    print(str(excinfo))
    from stocksdashboard.stocksdashboard import StocksDashboard

try:
    from .formatter import Formatter
except Exception as excinfo:
    print(str(excinfo))
    from formatter import Formatter

class DashboardWithWidgets:
    def __init__(self, sdb, sliders_params, signals_expressions):
        global _widget_type
        _widget_type = (Slider, PreText)
        self.sliders = {}
        self.pretext = {}
        assert(isinstance(sdb, StocksDashboard))
        self.sdb = sdb
        self.sliders_params = sliders_params
        self.__check_sliders()
        self.signals_expressions = signals_expressions

    def __check_sliders(self):
        assert(self.sliders_params is not None)
        assert(isinstance(self.sliders_params, dict)), (
            "'sliders_params' should be" +
            " a dictionary with format, i.e.: " +
            "\{name_of_var: \{'title' : 'EMA'," +
            "'params': \{value':20, " +
            "'start':2, 'end':252, 'step':5\}\}\}")
        for k, v in list(self.sliders_params.items()):
            assert isinstance(v, dict), (
                "%s should contain a dict" % k +
                " as value. Found type %s: %s" % (type(v), v))
            assert(all([field in list(v.keys())
                        for field in ('title', 'params')])), (
                "'sliders_params should contain a dict containing:" +
                " ('title', 'expression', 'params'). " +
                "Found: %s" % v.keys())
            # "'expression': {'EMA': 'STOCK.ewm(span=w, min_periods=1,'" +
            # "'adjust=True,ignore_na=False)' " +
            # "'.mean()'\}"

    def create_sliders(self):
        # Sliders
        sliders = {}
        for name, args in list(self.sliders_params.items()):
            sliders[name] = Slider(title=args['title'], **args['params'])
        self.sliders = sliders
        return sliders

    @staticmethod
    def replace_var(expr, varname, dict_name):
        return expr.replace(varname, "%s[%s]" % (dict_name, varname))

    def update_expression(self, var_dict, expression, dict_name,
                          expr=["(?<=\()(\w+)(?=\))",
                                "(?<==)(\w+)+(?=,)"]):
        global _widget_type
        expression_temp = copy.deepcopy(expression)
        replaced = set()
        for e in expr:
            for word in re.findall(e, expression_temp):
                if word in list(var_dict.keys()) and word not in replaced:
                    word_pattern = e.replace('\\w+', '\\b' + word)
                    word_replacement = "%s['%s']" % (dict_name, word)
                    if isinstance(var_dict[word], _widget_type):
                        word_replacement = word_replacement + '.value'
                    expression_temp = re.sub(
                        word_pattern, word_replacement, expression_temp)
                    replaced.add(word)
        return expression_temp

    def _format_signal_expressions(self, data_temp):
        signals_expressions_formatted = {}
        for signal_name, expr in list(self.signals_expressions.items()):
            expression_temp = copy.deepcopy(expr)
            expression_temp = self.update_expression(
                data_temp,
                expression_temp, 'data_temp',
                ["(\w+)(?=\W+)", "(?<=\W)(\w+)(?=\W+)", "(?<=\()(\w+)(?=\))",
                 "(?<==)(\w+)+(?=,)"])
            expression_temp = self.update_expression(
                self.sliders,
                expression_temp, 'self.sliders',
                ["(\w+)(?=\W+)", "(?<=\()(\w+)(?=\))", "(?<==)(\w+)+(?=,)"])
            signals_expressions_formatted[signal_name] = copy.deepcopy(
                expression_temp)
        self.signals_expressions_formatted = copy.deepcopy(
            signals_expressions_formatted)

        return signals_expressions_formatted

    def update_data(self, attrname, old, new):
        sliders_values = {}
        data_temp = {}
        result = {}
        for k, v in list(self.sliders.items()):
            sliders_values[k] = v.value
        for i, __data_source in enumerate(self.sdb.datasources):
            for name in list(__data_source.data.keys()):
                if re.findall("\(\w+\)", name):
                    raise(ValueError("Variable should not contain " +
                                     "plain parentheses. "
                                     "If included use '\(' and '\)'." +
                                     "Found: %s" % name))
                if len(__data_source.data[name]) > 1:
                    data_temp[name] = pd.Series(__data_source.data[name],
                                                index=__data_source.data['x'])
                else:
                    data_temp[name] = __data_source.data[name]
        if not hasattr(self, 'signal_expressions_formatted'):
            self._format_signal_expressions(data_temp)
        for signal_name, expr in list(self.signals_expressions.items()):
            result[signal_name] = eval(
                self.signals_expressions_formatted[signal_name])

        for i, __data_source in enumerate(self.sdb.datasources):
            for name in result:
                if name in __data_source.data:
                    (__data_source.data['x'],
                     __data_source.data[name]
                     ) = Formatter._get_x_y(result[name])

    def widget_on_change(self):
        list_of_widgets = list(self.sliders.values())
        for _widget in list_of_widgets:
            # print(w)
            if isinstance(_widget, PreText):
                attribute_name = 'text'
            else:
                attribute_name = 'value'
            _widget.on_change(attribute_name, self.update_data)
