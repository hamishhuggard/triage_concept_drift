import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from detection import *

class DataStream:

    STREAM_COUNT = -1
    def get_panel_id():
        DataStream.STREAM_COUNT += 1
        return f'Plot-{DataStream.STREAM_COUNT}'

    def __init__(self, x=[], y=[], status=[], id=None, two_tailed=False, title=''):

        if id:
            self.id_ = id
        else:
            self.id_ = DataStream.get_panel_id()

        self.title = title
        self.two_tailed = two_tailed

        # This is the x and y which will be displayed
        self.x = self.X = x
        self.y = self.Y = y
        self.status = self.STATUS = status

    def get_plot(self):
        return dcc.Graph(id = self.id_)

    def get_figure(self):
        figure = { 'data': self.get_data() }
        if len(self.title) > 0:
            title = self.title + ' '
        figure['layout'] = {'title': f'{title} ({self.get_status()})'}
        return figure

    def get_data(self):
        marker = {}#'label': self.X}
        color_dict = {'Drift': 'red', 'Warning': 'orange', 'Normal': 'green'}
        if len(self.status) > 0:
            marker['color'] = [ color_dict[s] for s in self.status ]
        text = [ 'Incorrect' if i else 'Correct' for i in self.Y ]
        text = [
            'Prediction: ' + a + \
            '<br>Drift Status: ' + b + \
            '<extra></extra>' # This suppresses some extra text that says "trace-1"
            for a,b in zip(text, self.STATUS)
        ]
        return [
            go.Scatter(
                x=self.x,
                y=self.y,
                text=text,
                mode='lines+markers',
                marker=marker,
                line={'color': 'grey'},
                hovertemplate="%{text}"
            )
        ]

    def apply_drift_detector(self):
        pass

    def get_status(self):
        return list(self.status)[-1]

    def get_drift_magnitude(self):
        pass

    def run_drift_detector(self):
        self.status = []

class CategoryStream(DataStream):

    def __init__(self, title, streams):
        self.streams = streams
        super().__init__(self, title=title)

    def get_data(self):
        data = []
        for stream in self.streams:
            stream_scatter = [
                go.Scatter(
                    x=stream.x,
                    y=stream.y,
                    mode='lines',
                    name=stream.title,
                    stackgroup='one'
                )
            ]
            data.extend(stream_scatter)
        return data



class MultiStreamPlot(html.Div):

    '''
    Takes care of pagination and sorting by driftiness.
    '''

    def __init__(self, x, ys, id, title):
        '''
        x is a list of x values
        ys is a dictionary {category_value: y_values}
        '''
        self.id = id
        self.title = title
        self.x = x
        self.ys = ys
        self.plots = [ DataStream(x, y, id=val, title=val) for (val, y) in ys.items() ]
        super().__init__(
            [
                html.H2(title),
                html.Br(),
            ] + self.plots
        )

class CategoryPlots(MultiStreamPlot):

    def __init__(self, x, ys, id, title):
        '''
        x is a list of x values
        ys is a dictionary {category_value: y_values}
        '''
        super().__init__(x, ys, id, title)
        self.plots += CategoryPlot(self.plots)
