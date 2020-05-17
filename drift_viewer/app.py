from panels import *
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
smoother.connect_output(detections)
smoothing_panel = ControlPanel("Smoothing", [smoother])

data_panel = ControlPanel([stream_reader])

####################
### LOADING DATA ###
####################

def load_data():
    pass



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

accuracy_tab = dcc.Tab(get_plots([detections]), label='Error Rate')

predictions_div = html.Div(smoothed_predictions.get_plot())
labels_div = html.Div(smoothed_labels.get_plot())
label_tab = dcc.Tab([predictions_div.get_plot(), labels_div.get_plot()])

feature_tab = dcc.Tab(smoothed_features)

tabs = dcc.Tabs(
    [accuracy_tab],#, label_tab, feature_tab],
    id="tabs",
    content_style={
        'borderLeft': '1px solid #d6d6d6',
        'borderRight': '1px solid #d6d6d6',
        'borderBottom': '1px solid #d6d6d6',
        'padding': '44px'
    }
)

app = dash.Dash()

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
