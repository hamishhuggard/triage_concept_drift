import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
from dash_core_components import Link
import dash_html_components as html

class DataStream:

    STREAM_COUNT = -1
    def get_panel_id():
        DataStream.STREAM_COUNT += 1
        return f'Plot-{DataStream.STREAM_COUNT}'

    def __init__(self, path):

        self.id_ = DataStream.get_panel_id()

        self.path = path
        self.title = re.match('.+/(\w+).csv', path).group(1)
        content = pd.read_csv(path)

        self.x = self.X = list(content.index)
        self.y = self.Y = np.array(content.value, dtype='float32')
        self.status = self.STATUS = content.status
        self.description = self.DESCRIPTION = content.description

    def get_plot(self):
        return dcc.Graph(id = self.id_)

    def get_figure(self):
        figure = { 'data': self.get_data() }
        if len(self.title) > 0:
            title = self.title + ' '
        figure['layout'] = {'title': f'{title} ({self.get_status()})'}
        # If this is a binary variable, set the limits of the y-axis to about 0 and 1
        if ((0 == np.array(self.Y)) | (np.array(self.Y) == 1)).all():
            figure['layout']['yaxis'] = dict(range=[-0.1,1.1])
        return figure

    def get_data(self):

        # Color the scatter points by their drift status
        marker = {}
        color_dict = {'DRIFT': 'red', 'WARNING': 'orange', 'NORMAL': 'green'}
        if len(self.status) > 0:
            marker['color'] = [ color_dict[s] for s in self.status ]

        # The hovertext for each scatter point
        text = [
            'Value: ' + str(int(a)) + \
            '<br>Drift Status: ' + b + \
            '<br>Description: ' + c + \
            '<extra></extra>' # This suppresses some extra text that says "trace-1"
            for a,b,c in zip(self.Y, self.STATUS, self.DESCRIPTION)
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

    def get_status(self):
        return list(self.status)[-1]

    def get_self_link(self):
        return Link(self.title, href=f'#{self.id_}')

    def __cmp__(self, other):

        sstatus = self.get_status()
        ostatus = other.get_status()

        # Convert these to priority integers
        status2int = {
            'DRIFT': 2,
            'WARNING': 1,
            'NORMAL': 0
        }
        sstatus = status2drift[sstatus]
        ostatus = status2drift[ostatus]

        # If they have the same status then use alphabetic order with titles
        if sstatus == ostatus:
            return self.title.__cmp__(other.title)

        # Otherwise whichever has the higher priority integer
        return sstatus - ostatus

    def __repr__(self):
        return self.title

    @staticmethod
    def get_streams_by_status(stream_list, status):
        ret = []
        for stream in stream_list:
            if stream.get_status() == status:
                ret.append(stream)
        return ret

class AccuracyStream(DataStream):

    acc_stream = []

    def __init__(self, path):
        super().__init__(path)
        AccuracyStream.acc_stream = self

    @staticmethod
    def get_long_status_div():
        return ''

    @staticmethod
    def get_status_div():
        # return html.Div('hello', style={'color': 'red'})#'color', '#7FDBFF'})
        status = AccuracyStream.acc_stream.get_status()
        if status == 'DRIFT':
            return html.Div('Concept drift detected', style={'color': 'red'})
        elif status == 'WARNING':
            return html.Div('Concept drift suspected', style={'color': 'orange'})
        else:
            return html.Div('No concept drift', style={'color': 'green'})


class FeatureStream(DataStream):

    streams = []
    def register(self):
        FeatureStream.streams.append(self)

    def __init__(self, path):
        super().__init__(path)
        self.register()

    @staticmethod
    def get_status_div():
        stream_list = FeatureStream.streams
        drift = DataStream.get_streams_by_status(stream_list, 'DRIFT')
        warning = DataStream.get_streams_by_status(stream_list, 'WARNING')
        if len(drift) > 0:
            return html.Div('Feature drift detected.', style={'color': 'red'})
        elif len(warning) > 0:
            return  html.Div('Feature drift suspected.', style={'color': 'orange'})
        else:
            return html.Div('No feature drift.', style={'color': 'green'})

    @staticmethod
    def get_long_status_div():
        stream_list = FeatureStream.streams
        drift = DataStream.get_streams_by_status(stream_list, 'DRIFT')
        warning = DataStream.get_streams_by_status(stream_list, 'WARNING')
        if len(drift)==0 and len(warning)==0:
            return html.Div('No feature drift.', style={'color': 'green'})
        children = []
        if len(warning) > 0:
            children.append(
                html.Div(
                    'Suspected feature drift on: ' + \
                    ', '.join(stream.title for stream in warning),
                    style={'color': 'orange'}
                )
            )
        if len(drift) > 0:
            children.append(
                html.Div(
                    'Feature drift on: ' + \
                    ', '.join(stream.title for stream in drift),
                    style={'color': 'red'}
                )
            )
        return html.Div(children)


class LabelStream(DataStream):

    streams = []
    def register(self):
        LabelStream.streams.append(self)

    def __init__(self, path):
        super().__init__(path)
        self.register()

    @staticmethod
    def get_status_div():
        stream_list = LabelStream.streams
        drift = DataStream.get_streams_by_status(stream_list, 'DRIFT')
        warning = DataStream.get_streams_by_status(stream_list, 'WARNING')
        if len(drift) > 0:
            return html.Div('Label drift detected.', style={'color': 'red'})
        elif len(warning) > 0:
            return  html.Div('Label drift suspected.', style={'color': 'orange'})
        else:
            return html.Div('No label drift.', style={'color': 'green'})

    @staticmethod
    def get_long_status_div():
        stream_list = LabelStream.streams
        drift = DataStream.get_streams_by_status(stream_list, 'DRIFT')
        warning = DataStream.get_streams_by_status(stream_list, 'WARNING')
        if len(drift)==0 and len(warning)==0:
            return html.Div('No label drift.', style={'color': 'green'})
        children = []
        if len(warning) > 0:
            children.append(
                html.Div(
                    'Suspected label drift on: ' + \
                    ', '.join(stream.title for stream in warning),
                    style={'color': 'orange'}
                )
            )
        if len(drift) > 0:
            children.append(
                html.Div(
                    'Label drift on: ' + \
                    ', '.join(stream.title for stream in drift),
                    style={'color': 'red'}
                )
            )
        return html.Div(children)
