import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re

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

        # print(self.title, 'loaded csv')
        # print(content.head())

        self.x = self.X = list(content.index)
        self.y = self.Y = content.value
        self.status = self.STATUS = content.status
        self.description = self.DESCRIPTION = content.description

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
        color_dict = {'DRIFT': 'red', 'WARNING': 'orange', 'NORMAL': 'green'}
        if len(self.status) > 0:
            marker['color'] = [ color_dict[s] for s in self.status ]
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
        return list(self.STATUS)[-1]

# class CategoryStream(DataStream):
#
#     def __init__(self, title, streams):
#         self.streams = streams
#         super().__init__(self, title=title)
#
#     def get_data(self):
#         data = []
#         for stream in self.streams:
#             stream_scatter = [
#                 go.Scatter(
#                     x=stream.x,
#                     y=stream.y,
#                     mode='lines',
#                     name=stream.title,
#                     stackgroup='one'
#                 )
#             ]
#             data.extend(stream_scatter)
#         return data
#


# class MultiStreamPlot(html.Div):
#
#     '''
#     Takes care of pagination and sorting by driftiness.
#     '''
#
#     def __init__(self, x, ys, id, title):
#         '''
#         x is a list of x values
#         ys is a dictionary {category_value: y_values}
#         '''
#         self.id = id
#         self.title = title
#         self.x = x
#         self.ys = ys
#         self.plots = [ DataStream(x, y, id=val, title=val) for (val, y) in ys.items() ]
#         super().__init__(
#             [
#                 html.H2(title),
#                 html.Br(),
#             ] + self.plots
#         )
#
# class CategoryPlots(MultiStreamPlot):
#
#     def __init__(self, x, ys, id, title):
#         '''
#         x is a list of x values
#         ys is a dictionary {category_value: y_values}
#         '''
#         super().__init__(x, ys, id, title)
#         self.plots += CategoryPlot(self.plots)
