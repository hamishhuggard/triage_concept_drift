from panels import *
import sys
from plots import *
from glob import glob
# from stream_reading import StreamReader

######################
### CONTROL PANELS ###
######################

# stream_reader = StreamReader("Choose a Datastream")

# detections = stream_reader.get_accuracy()

# Truncation panel

feature_truncator = Truncator("Features Truncation (%)")
prediction_truncator = Truncator("Predictions Truncation (%)")
label_truncator = Truncator("Labels Truncation (%)")

truncating_panel = ControlPanel(
    "Truncate Data Streams",
    [feature_truncator, label_truncator, prediction_truncator]
)

# Smoothing panel

smoother = Smoother()
smoothing_panel = ControlPanel("Smoothing", [smoother])

# data_panel = ControlPanel([stream_reader])

####################
### LOADING DATA ###
####################




#################
### LOGICS    ###
#################

# features = stream_reader.get_features()
# labels = stream_reader.get_labels()
# loss = stream_reader.get_loss()

# # Truncate data streams
# feature_truncator.connect_outputs(features)
# label_truncator.connect_outputs(labels)
# predictions_truncator.connect_outputs(predictions)
#
# # Smooth data streams
# smoother.connect_outputs(features)
# smoother.connect_outputs(labels)
# smoother.connect_outputs(predictions)


##############
### LAYOUT ###
##############

def get_plots(streams):
    return [ stream.get_plot() for stream in streams ]


def load_data(dir):
    global app, smoother, feature_truncator, prediction_truncator, label_truncator

    loss_path = os.path.join(dir, 'loss.csv')
    loss_stream = DataStream(loss_path)

    feature_streams = []
    for feature_path in glob(dir+'/features/*.csv'):
        feature_streams.append(DataStream(feature_path))
    label_streams = []
    for label_path in glob(dir+'/predictions/*.csv'):
        label_streams.append(DataStream(label_path))

    feature_truncator.connect_output(loss_stream)
    prediction_truncator.connect_outputs(label_streams)
    label_truncator.connect_outputs(feature_streams)

    smoother.connect_output(loss_stream)
    smoother.connect_outputs(label_streams)
    smoother.connect_outputs(feature_streams)

    accuracy_tab = dcc.Tab(loss_stream.get_plot(), label='Error Rate')

    label_tab = dcc.Tab(get_plots(label_streams), label='Labels')

    feature_tab = dcc.Tab(get_plots(feature_streams), label='Features')

    tabs = dcc.Tabs(
        [accuracy_tab, label_tab, feature_tab],
        id="tabs",
        content_style={
            'borderLeft': '1px solid #d6d6d6',
            'borderRight': '1px solid #d6d6d6',
            'borderBottom': '1px solid #d6d6d6',
            'padding': '44px'
        }
    )

    app.layout = html.Div([
        html.Div([
            html.H1('GP Referrals Triage Drift Detection', style={'margin': '48px 0'}),
            html.Div(
                [
                    truncating_panel,
                    html.Br(),
                    smoothing_panel
                ],
                style={'float': 'left', 'width': '30%'}
            ),
            tabs,
        ],
        style={
            'textAlign': 'center',
            'fontFamily': 'system-ui',
            # 'maxWidth': '1000px',
            'margin': '0 auto'
        }
        )
    ])

app = dash.Dash()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError('There should be one command line arguments specifying the location of the drift detector status directory.')
    load_data(sys.argv[1])

#################
### CALLBACKS ###
#################
@app.callback(
    CallBackLogic.get_outputs(),
    CallBackLogic.get_inputs()
)
def update_plots(*args):
    CallBackLogic.update(*args)
    return CallBackLogic.get_return()

if __name__ == '__main__':
    app.run_server(debug=True)
