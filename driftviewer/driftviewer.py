from layout import get_layout
from panels import CallBackLogic
import sys
import dash

if __name__ == '__main__':

    app = dash.Dash()

    # Layout
    if len(sys.argv) != 2:
        raise ValueError('There should be one command line arguments specifying the location of the drift detector status directory.')
    dir = sys.argv[1]

    app.layout = get_layout(dir)

    # Callbacks
    @app.callback(
        CallBackLogic.get_outputs(),
        CallBackLogic.get_inputs()
    )
    def update_plots(*args):
        CallBackLogic.update(*args)
        return CallBackLogic.get_return()

    app.run_server(debug=False)
