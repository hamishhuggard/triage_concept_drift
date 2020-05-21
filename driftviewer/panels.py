import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output

import pandas as pd
import numpy as np
import itertools

from collections import Counter
import re
import os

from plots import *

###################################################
### CONTROLS TO POPULATE A CONTROL PANEL        ###
###################################################

'''
Control panels are arranged in a tree structure, where PanelItems are the leaves.
TODO: take out the smooth() function etc and put it into the constructor
'''

class PanelItem:

    '''
    Any item like a slider, a button, or a dropdown menu which
    could go in a control panel. Basically this object keeps
    track of the id of the corresponding html object, and the
    current value of the item.
    '''

    PANEL_COUNTER = Counter()
    def get_new_id(self):
        type_ = re.search("panels.(\w+)'", str(type(self))).group(1)
        type_counter = PanelItem.PANEL_COUNTER
        type_counter[type_] += 1
        return f'{type_}-{type_counter[type_]}'

    def get_id(self):
        if hasattr(self, 'id_'):
            return self.id_
        else:
            self.id_ = self.get_new_id()
            return self.id_


class PercentSlider(PanelItem, dcc.Slider):

    '''
    A slider from 0 to 100.
    '''

    def __init__(self, value=100):

        dcc.Slider.__init__(
            self,
            id=self.get_id(),
            min=0,
            max=100,
            marks={i: str(i) for i in range(101) if i % 100 == 0 },
            value=value
        )
        self.value = value

class DropDownItem(PanelItem, dcc.Dropdown):

    '''
    A drop down menu.
    '''

    def __init__(self, options=[], value=None):

        dcc.Dropdown.__init__(
            self,
            id=self.get_id(),
            options=options,
            value=value
        )
        self.value = value

###################################################
### CONTROL PANEL                               ###
###################################################

class CallBackLogic:

    '''
    This object makes Dash callback logic less annoying. If
    you have several inputs from PanelItems influencing several
    output html objects, then CallBackLogic makes sure everything
    which _should be_ updated _is_ updated.
    '''

    ### STATIC LOGIC ###

    inputs = {}
    outputs = {}
    logics = []

    @staticmethod
    def get_inputs():
        return [
            Input(component_id=id, component_property='value')
            for id in CallBackLogic.inputs.keys()
        ]

    @staticmethod
    def get_outputs():
        return [
            Output(component_id='status', component_property='children')
        ] + \
        [
            Output(component_id=id, component_property='figure')
            for id in CallBackLogic.outputs.keys()
        ]

    @staticmethod
    def update(*args):
        for input, val in zip(CallBackLogic.inputs.values(), args):
            input.value = val
        for logic in CallBackLogic.logics:
            logic.update_outputs()

    @staticmethod
    def get_return():
        return [
            html.Div([
                AccuracyStream.get_status_div(),
                FeatureStream.get_status_div(),
                LabelStream.get_status_div()
            ])
        ] + \
        [
            stream.get_figure() for stream in CallBackLogic.outputs.values()
        ]

    ### INSTANCE LOGIC ###

    def __init__(self):
        self.outputs = set()
        self.inputs = set()
        CallBackLogic.logics.append(self)

    def connect_output(self, output):
        self.connect_outputs([output])

    def connect_outputs(self, outputs):
        self.outputs.update(outputs)
        for output in outputs:
            CallBackLogic.outputs[output.id_] = output

    def connect_input(self, input):
        self.connect_inputs([input])

    def connect_inputs(self, inputs):
        self.inputs.update(inputs)
        for input in inputs:
            CallBackLogic.inputs[input.id_] = input

    def update_output(self):
        pass

    def update_outputs(self):
        for output in self.outputs:
            self.update_output(output)

class ControlPanel(html.Div): # , CallBackLogic

    def __init__(self, title, children):

        super().__init__(
            # self,
            [
                html.Br(),
                html.H2(title),
                html.Div(
                    children,
                    style={'width': '80%', 'margin': '10px auto'}
                ),
                html.Br()
            ],
            style={'margin': '0 auto', 'border-radius': '10px',
                'background-color': '#CCC', 'width': '95%'} # 'width': '90%',
        )

###################################################
### CONTROLS                                    ###
###################################################

class Truncator(CallBackLogic, html.Div):

    def __init__(self, title=''):
        self.slider = PercentSlider(value=100)
        CallBackLogic.__init__(self)
        html.Div.__init__(self, [html.H5(title), self.slider])
        self.connect_input(self.slider)

    def update_output(self, output):
        upto = self.slider.value
        # convert upto from percentage to index
        stream_len = len(output.X)
        upto = int( stream_len * upto / 100 )
        # truncate x and y values
        output.x = output.X[:upto]
        output.y = output.Y[:upto]
        output.status = output.STATUS[:upto]

class Smoother(CallBackLogic, html.Div):

    SMOOTH_SHAPES = ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']

    @staticmethod
    def smooth(x, win_width, win_shape):
        '''
        Smooth an array 'x' using a sliding window of width win_width
        and shape win_shape.
        This code is based on http://www.scipy.org/Cookbook/SignalSmooth
        '''
        # Convert win_width from percentage to absolute
        win_width = int(len(x) * win_width / 100)

        # Window widths this small can cause problems
        if win_width < 3:
            return x

        # Can't smooth an empty array
        if len(x) == 0:
            return []

        # Having a window width longer than the length of x reduces x's length
        if win_width > len(x):
            win_width = len(x)

        # Pad x so that convolutional window will reflect off the edges
        s = np.r_[x[::-1][-win_width:], x,
                    x[::-1][:win_width]]

        # Array to convolve with
        if win_shape == 'flat':
            w=np.ones(win_width,'d')
        else:
            w=eval('np.'+win_shape+'(win_width)')

        y=np.convolve(w/w.sum(), s, mode='same')
        return y[win_width:-win_width]

    def __init__(self, title="Curve Smoothing"):

        self.slider = PercentSlider(20)

        dropdown_opts = [ {'label': i, 'value': i} for i in Smoother.SMOOTH_SHAPES ]
        self.dropdown = DropDownItem(options=dropdown_opts, value='hanning')

        CallBackLogic.__init__(self)

        html.Div.__init__(
            self,
            [
                html.H5('Smoothing Kernel'),
                self.dropdown,
                html.H5('Smoothness'),
                self.slider
            ]
        )

        self.connect_inputs([self.slider, self.dropdown])

    def update_output(self, output):
        y = output.y
        win_width = self.slider.value
        win_shape = self.dropdown.value
        output.y = Smoother.smooth(y, win_width, win_shape)
