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
### DATA READER                                 ###
###################################################

class StreamReader:

    '''
    Given a directory with three csvs:
     * bow_features.csv
        * each column represents a token. The values are Boolean and indicate
        whether that token occurred in that document.
     * cat_features.csv
        * each column represents a categorical feature. The values are strings
        of the category the instance belongs to.
     * Maybe in the future: num_features.csv, bool_features.csv
     * predictions.csv
        * one column giving the predictions of the model
     * labels.csv
        * only one column giving the true labels

    StreamReader extracts the data from each of these csvs and creates DataStream objects.
    Within the DataStream constructor, drift statuses will be calculated.
    '''

    def __init__(self, title=''):
        self.dirname = os.path.abspath(f'../Tornado/data_streams/new_concept')

    def parse_cat_datastream(self, stream):
        # get unique values
        unique = list(unique)

    def load_all_data(self):
        self.bow_features = pd.read_csv(dirname + '/bow_features.csv')
        self.cat_features = pd.read_csv(dirname + '/cat_features.csv')
        self.predicitons = pd.read_csv(dirname + '/predictions.csv')
        self.labels = pd.read_csv(dirname + '/labels.csv')

    def get_features(self):
        data = pd.read_csv(dirname + '/test.csv')
    def get_labels(self):
        with open(dirname + '/y.json', 'r') as f:
            y = json.loads(f.read())
        for i in range(1, 6): # range of possible triage labels
            pass

    def get_accuracy(self):
        # status_data = pd.read_csv(dirname + '/status_data.csv')
        err_data = pd.read_csv(self.dirname + '/err_data.csv')
        errs = err_data['ERRS']
        status = err_data['STATUS']
        # p = err_data['']
        ds =  DataStream(x=np.arange(len(errs)), y=errs, title='Error Rate', status=status)
        return ds

class StreamReader(CallBackLogic, html.Div):

    def __init__(self, title=''):

        dropdown_opts = [ {'label': i, 'value': i} for i in Smoother.SMOOTH_SHAPES ]
        self.dropdown = DropDownItem(options=dropdown_opts, value='hanning')

        CallBackLogic.__init__(self)
        html.Div.__init__(self, [html.H5(title), self.slider])
        self.connect_input(self.slider)

# def load_scenario(i):
#     # path = os.path.abspath(f'./fake_data/scenario{i}.csv')
#     # data = pd.read_csv(path)
#     # data['date'] = data['date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%S:%f'))
#     dirname = os.path.abspath(f'../experiments/data_streams/scenarios/{i}/')
#     data = pd.read_csv(dirname + '/test.csv')
#     with open(dirname + '/y.json', 'r') as f:
#         y = json.loads(f.read())
#     with open(dirname + '/errs.json', 'r') as f:
#         errs = json.loads(f.read())
#     err_data = pd.read_csv(dirname + '/err_data.csv')
#     status_data = pd.read_csv(dirname + '/status_data.csv')
#     for i in [1,2,3,4,5]:
#         data[f'label={i}'] = [ label==i for label in y ]
#     data['error_rate'] = errs
#     data['date'] = list(range(len(data)))
#     # data['err_data'] = err_data
#     data = data.join(err_data)
#     data = data.join(status_data)
#     return data

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
        # win_width = int(len(x) * win_width / 800)
        x = np.array(x, dtype='int')
        if win_width < 3:
            return x
        if len(x) == 0:
            return []
        s = np.r_[x[win_width-1::-1], x,
                    x[-1:-win_width:-1]]
        if win_shape == 'flat': #moving average
                w=np.ones(win_width,'d')
        else:
                w=eval('np.'+win_shape+'(win_width)')
        y=np.convolve(w/w.sum(), s, mode='same')
        return y[win_width:-win_width+1]
        # y = np.convolve(w/w.sum(), x, mode='same')
        return y

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
        output.y = Smoother.smooth(y, win_width*2, win_shape)
