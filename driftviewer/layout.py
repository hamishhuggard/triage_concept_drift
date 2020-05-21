from panels import *
from plots import *
from glob import glob
import dash_html_components as html

def get_plots(streams):
    return [ stream.get_plot() for stream in streams ]

def get_layout(dir):

    ####################
    ### LOADING DATA ###
    ####################

    acc_path = os.path.join(dir, 'accuracy.csv')
    acc_stream = AccuracyStream(acc_path)

    feature_streams = []
    for feature_path in sorted(list(glob(dir+'/features/*.csv'))):
        feature_streams.append(FeatureStream(feature_path))
    label_streams = []
    for label_path in sorted(list(glob(dir+'/predictions/*.csv'))):
        label_streams.append(LabelStream(label_path))

    ######################
    ### CONTROL PANELS ###
    ######################

    # Truncation panel
    accuracy_truncator = Truncator("Accuracy Truncation", max_val=len(acc_stream.x))
    feature_truncator = Truncator("Features Truncation", max_val=len(feature_streams[0].x))
    label_truncator = Truncator("Labels Truncation", max_val=len(label_streams[0].x))

    truncating_panel = ControlPanel(
        "Truncate Data Streams",
        [accuracy_truncator, label_truncator, feature_truncator]
    )

    # Smoothing panel
    smoother = Smoother()
    smoothing_panel = ControlPanel("Smoothing", [smoother])

    #################
    ### LOGICS    ###
    #################

    accuracy_truncator.connect_output(acc_stream)
    feature_truncator.connect_outputs(feature_streams)
    label_truncator.connect_outputs(label_streams)

    smoother.connect_output(acc_stream)
    smoother.connect_outputs(label_streams)
    smoother.connect_outputs(feature_streams)

    ##############
    ### LAYOUT ###
    ##############

    accuracy_tab = dcc.Tab([html.Div(id='acc-status'), acc_stream.get_plot()], label='Accuracy', id='accuracy-tab')

    label_tab = dcc.Tab([html.Div(id='label-status')] + get_plots(label_streams), label='Labels', id='label-tab')

    feature_tab = dcc.Tab([html.Div(id='feature-status')] + get_plots(feature_streams), label='Features', id='feature-tab')

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

    return html.Div([
        html.Div([
            html.H1('Multiple Drift Detector', style={'margin': '48px 0'}),
            html.Div(
                [
                    ControlPanel('Status', html.Div(id='status')),
                    html.Br(),
                    smoothing_panel,
                    html.Br(),
                    truncating_panel,
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
