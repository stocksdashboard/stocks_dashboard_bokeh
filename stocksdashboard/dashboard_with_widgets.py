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
from functools import partial

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
        return expression_temp, replaced

    def _format_signal_expressions(self, data_temp):
        signals_expressions_formatted = {}
        widgets_to_signals = {}
        signals_to_signals = {}
        for signal_name, expr in list(self.signals_expressions.items()):
            expression_temp = copy.deepcopy(expr)
            expression_temp, replaced = self.update_expression(
                data_temp,
                expression_temp, 'data_temp',
                ["(\w+)(?=\W+|$)", "(?<=\W)(\w+)(?=\W+|$)",
                 "(?<=\()(\w+)(?=\))", "(?<==)(\w+)+(?=,)"])
            expression_temp, sliders_replaced = self.update_expression(
                self.sliders,
                expression_temp, 'self.sliders',
                ["(\w+)(?=\W+)", "(?<=\()(\w+)(?=\))", "(?<==)(\w+)+(?=,)"])
            signals_expressions_formatted[signal_name] = copy.deepcopy(
                expression_temp)
            signals_to_signals[signal_name] = copy.deepcopy(replaced)
            # Save dict of widgets related to signals
            for s in sliders_replaced:
                if s in widgets_to_signals:
                    widgets_to_signals[s].add((signal_name))
                else:
                    widgets_to_signals[s] = {signal_name}
        # Iterate over all the replacements
        for signal_name, replaced in list(signals_to_signals.items()):
            # For each signal check all the variables
            for r in replaced:
                # if any of the variables is in a slider,
                # then our variable is dependent of the slider.
                for slider, l in list(widgets_to_signals.items()):
                    if r in l:
                        widgets_to_signals[slider].add(signal_name)
        self.signals_expressions_formatted = copy.deepcopy(
            signals_expressions_formatted)
        self.signals_to_signals = copy.deepcopy(signals_to_signals)
        self.widgets_to_signals = copy.deepcopy(widgets_to_signals)
        return (signals_expressions_formatted, widgets_to_signals,
                signals_to_signals)

    def update_data(self, attrname, old, new, widget_name):
        sliders_values = {}
        data_temp = {}
        result = {}
        selected_signals = None

        if hasattr(self, 'signals_to_signals'):
            selected_signals = set([
                s for k in self.widgets_to_signals[widget_name]
                for s in list(self.signals_to_signals[k])])
            # if s not in self.widgets_to_signals[widget_name]])
            prev_selected = {}
            # Run until all dependent variables are tracked
            while prev_selected != selected_signals:
                dependent_signals = set([
                    _s for s in selected_signals
                    if (s in self.signals_to_signals)
                    # if (s in self.signals_to_signals and
                    #     s not in self.widgets_to_signals[widget_name])
                    for _s in self.signals_to_signals[s]])
                prev_selected = copy.deepcopy(selected_signals)
                selected_signals = selected_signals.union(
                    set(dependent_signals))
            # print(widget_name, self.widgets_to_signals[widget_name],
            #      selected_signals, )
            selected_signals = selected_signals.union(
                self.widgets_to_signals[widget_name])
            # avoid signals that
            # are in the expression signals
            # changed by the widget
            # print(widget_name, selected_signals)
        for k, v in list(self.sliders.items()):
            sliders_values[k] = v.value

        for i, __data_source in enumerate(self.sdb.datasources):
            for name in list(__data_source.data.keys()):
                # Search for the signal just in case
                # the process has not been done or
                # or if the singal is one of the selected ones
                # that are necessary for the signals changed by the widgets.
                if (not hasattr(self, 'signals_to_signals') or
                        (selected_signals and name in selected_signals)):
                    if re.findall("\(\w+\)", name):
                        raise(ValueError("Variable should not contain " +
                                         "plain parentheses. "
                                         "If included use '\(' and '\)'." +
                                         "Found: %s" % name))
                    if len(__data_source.data[name]) > 1:
                        data_temp[name] = pd.Series(
                            copy.deepcopy(__data_source.data[name]),
                            index=copy.deepcopy(__data_source.data['x']))
                    else:
                        data_temp[name] = copy.deepcopy(
                            __data_source.data[name])
        if not hasattr(self, 'signals_expressions_formatted'):
            self._format_signal_expressions(data_temp)
            signals = list(self.signals_expressions_formatted.keys())
        else:
            # signals = [s for s in self.widgets_to_signals[widget_name]]
            signals = [s for s in selected_signals
                       if s in list(self.signals_expressions_formatted.keys())]
        # print(signals)
        for i in range(2):
            for signal_name in signals:
                result[signal_name] = eval(
                    self.signals_expressions_formatted[signal_name])
                # Update result in data_temp. If it is not dependent
                # of other variable signal, this result won't change.
                data_temp[signal_name] = result[signal_name]
        for i, __data_source in enumerate(self.sdb.datasources):
            for name in result:
                if name in __data_source.data:
                    (__data_source.data['x'],
                     __data_source.data[name]
                     ) = copy.deepcopy(Formatter._get_x_y(result[name]))

    def widget_on_change(self):
        for k, _widget in list(self.sliders.items()):
            if isinstance(_widget, PreText):
                attribute_name = 'text'
            else:
                attribute_name = 'value'
            # _widget.on_change(attribute_name, self.update_data)
            _widget.on_change(attribute_name, partial(
                self.update_data, widget_name=k))
