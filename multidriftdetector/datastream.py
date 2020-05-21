import re
import os
from wasabi import color, Printer
import numpy as np
from copy import copy

class DataStream:

    '''
    This monitors a single stream of data (feature, label, model accuracy) for drift.
    '''

    # When a drift message is sent, should the status be colored?
    color_messages = True

    # If so, what should the color code be?
    message_colors = {
        'NORMAL': 'green',
        'WARNING': 'yellow',
        'DRIFT': 'red'
    }

    def __init__(
            self,
            detector, # The detection algorithm to be used on this stream
            drift_action=print, # The action to be taken when drift is detected
            name='unknown', # The name of this data stream
            bidirectional=True # Monitor for increases AND decreases in the rate of this stream, or only increases?
            ):
        self.drift_action = drift_action
        self.detector = detector
        self.status = 'NORMAL'
        self.name = name
        self.bidirectional = bidirectional
        self.detector2 = copy(detector) if bidirectional else None
        self.drift_direction = 'NORMAL'

    def add_value(self, value, conf=None):
        # Add a new value to this data stream
        # conf is confidence. This is for CDDM.

        # Once drift is detected no further updates are required.
        if self.status == 'DRIFT':
            return 'DRIFT'

        # Get the drift status of the data stream
        if conf:
            warning_status, drift_status = self.detector.detect(value, conf)
            if self.bidirectional:
                warning_status2, drift_status2 = self.detector2.detect(not value, conf)
            else:
                warning_status2, drift_status2 = False, False
        else:
            warning_status, drift_status = self.detector.detect(value)
            if self.bidirectional:
                warning_status2, drift_status2 = self.detector2.detect(not value)
            else:
                warning_status2, drift_status2 = False, False

        # Has the drift status changed? If so, in what direction?
        if drift_status or drift_status2:
            new_status = 'DRIFT'
            self.direction = 'INCREASE' if drift_status else 'DECREASE'
        elif warning_status or warning_status2:
            new_status = 'WARNING'
            self.direction = 'INCREASE' if warning_status else 'DECREASE'
        else:
            new_status = 'NORMAL'

        # If the status has changed then do a drift action.
        if new_status != self.status:
            message = f'The status of {self.name} has changed to '
            if DataStream.color_messages:
                bg_color = DataStream.message_colors[new_status]
                message += color(new_status, fg="black", bg=bg_color, bold=True)
            else:
                message += new_status
            self.drift_action(message)
            self.status = new_status

        return new_status

    def get_status(self):
        # What is the current status of the stream?
        return self.status
