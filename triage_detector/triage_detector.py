# from bow_machine import BOWMachine

# I don't know how to do this properly
import sys
import os
tornado_path = os.path.abspath('./tornado_med')
sys.path.insert(0, tornado_path)
from tornado_med.drift_detection.__init__ import *

from collections import defaultdict
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

class MultiDriftDetector:

    '''
    This object monitors for:
    - feature drift
    - label drift
    - real drift
    in a data stream.
    '''

    # The drift detection algorithms, used to detect feature drift, label drift, and concept drift, respectively.
    feature_dd=HDDM_A_test(warning_confidence=0.001, drift_confidence=0.0005)
    label_dd=copy(feature_dd)
    concept_dd=HDDM_A_test(warning_confidence=0.01, drift_confidence=0.005)

    def __init__(
            self,
            write_dir, # the directory to write the state of the detector
            drift_action=print # the action to take if drift is detected
        ):

        self.write_dir = write_dir
        self.drift_action = drift_action

        # Set up the directory for recording detector state
        root = self.root_dir = os.path.abspath(write_dir)
        fdir = self.feature_dir = os.path.join(root, 'features')
        pdir = self.predictions_dir = os.path.join(root, 'predictions')
        if not os.path.exists(fdir):
            os.makedirs(fdir)
        if not os.path.exists(pdir):
            os.makedirs(pdir)

        # Create the record of model loss
        self.loss_file = os.path.join(root, 'loss.csv')
        with open(self.loss_file, 'w') as f:
            f.write('value,status,description\n')
        self.loss_stream = DataStream(
            drift_action = self.drift_action,
            detector = copy(MultiDriftDetector.concept_dd),
            name = 'Concept Drift',
            bidirection=False # only detect increases in loss
        )

        # The prediction queue for matching predictions with labels
        self.prediction_queue = {}

    def init_file(self, fpath):
        '''
        Initialise the file (at fpath) which records the state of a given stream.
        Each stream has a csv with columns value, status, description.
        '''
        with open(fpath, 'w') as f:
            f.write('value,status,description\n')

    def append_file(self, fpath, value, status, description):
        '''
        When a new value is added to a data stream, append it to that stream's csv file.
        '''
        with open(fpath, 'a') as f:
            f.write(f'{value},{status},"{description}"\n')

    def set_features(self, feature_names):
        '''
        For each of the features in this setting, set up a csv file to record the
        state of that feature stream, and prepare a DataStream object.
        '''

        self.feature_names = feature_names

        # Set up a DataStream object to monitor each feature.
        self.feature_streams = {
            feature_name: DataStream(
                drift_action = self.drift_action,
                detector = copy(MultiDriftDetector.feature_dd),
                name = feature_name,
                bidirectional=True # detected changes in either direction
            ) for feature_name in feature_names
        }

        # Create the header for the feature files
        for feature_name in feature_names:
            feature_path = os.path.join(self.feature_dir, feature_name+'.csv')
            self.init_file(feature_path)

    def set_labels(self, label_names):
        '''
        For each of the label values in this setting, set up a csv file to record the
        state of that label stream, and prepare a DataStream object.
        '''

        self.label_names = label_names

        # Set up a DataStream object to monitor each label value.
        self.label_streams = {
            label_name: DataStream(
                drift_action = self.drift_action,
                detector = copy(MultiDriftDetector.label_dd),
                name = label_name,
                bidirectional=True
            ) for label_name in label_names
        }

        # Create the header for the feature files
        for label_name in label_names:
            label_path = os.path.join(self.predictions_dir, label_name+'.csv')
            self.init_file(label_path)

    def add_instance(self, instance, instance_id, description=''):
        '''
        When a new instance arrives (ie, referral doc), update the DataStream and
        csv file for each of the data streams.
        '''

        for feature_name, value in zip(self.feature_names, instance):
            feature_stream = self.feature_streams[feature_name]
            status = feature_stream.add_value(bool(value))
            feature_path = os.path.join(self.feature_dir, feature_name+'.csv')
            self.append_file(feature_path, value, status, description)


    def add_prediction(self, prediction, instance_id, description=''):
        '''
        When the model makes a new prediction, update the DataStream and csv file
        corresponding to the label value which the model is predicting. Then add
        the prediction to the prediction_queue so it can be matched with a true label later.
        '''

        # Which is the label that the model is predicting?
        label = self.label_names[np.argmax(prediction)]
        confidence = np.max(prediction)

        for label_name in self.label_names:
            value = label_name == label
            label_stream = self.label_streams[label_name]
            status = label_stream.add_value(value)
            label_path = os.path.join(self.predictions_dir, label_name+'.csv')
            self.append_file(label_path, value, status, description)

        self.prediction_queue[instance_id] = (label, confidence)

    def add_label(self, label, instance_id, description=''):
        '''
        When a new label arrives (ie priority label), match it with a model prediction
        from the prediction_queue, determine if the prediction was correct or not,
        and then update the loss DataStream and csv file.
        '''

        # retrieve from queue with confidence
        (prediction, confidence) = self.prediction_queue[instance_id]

        value = label == prediction

        if MultiDriftDetector.concept_dd.DETECTOR_NAME == 'CDDM':
            status = self.loss_stream.add_value(value, confidence)
        else:
            status = self.loss_stream.add_value(value)

        self.append_file(self.loss_file, value, status, description)


    def get_status(self):
        '''
        Print the overall status of the detector. That is,
        - the real drift status
        - the feature drift status
        - the label drift status
        '''

        # use a wasabi Printer for nice outputs
        msg = Printer()

        # Display concept drift status
        concept_status = self.loss_stream.get_status()
        if concept_status == 'DRIFT':
            msg.fail('Concept drift detected.')
        elif concept_status == 'WARNING':
            msg.warn('Concept drift suspected.')
        else:
            msg.good('Loss distribution normal.')

        # Display feature drift status
        warn_features = []
        drift_features = []
        for feature in self.feature_names:
            feature_status = self.feature_streams[feature].get_status()
            if feature_status == 'DRIFT':
                drift_features.append(feature)
            elif feature_status == 'WARN':
                warn_features.append(feature)
        if len(warn_features) > 0:
            msg.warn('Feature drift suspected on the following: '+', '.join(warn_features))
        if len(drift_features) > 0:
            msg.fail('Feature drift detected on the following: '+', '.join(drift_features))
        if len(drift_features)==0 and len(warn_features)==0:
            msg.good('Feature distribution normal.')

        # Display label drift status
        warn_labels = []
        drift_labels = []
        for label in self.label_names:
            label_status = self.label_streams[label].get_status()
            if label_status == 'DRIFT':
                drift_labels.append(label)
            elif label_status == 'WARN':
                warn_labels.append(label)
        if len(warn_labels) > 0:
            msg.warn('Label drift suspected on the following: '+', '.join(warn_labels))
        if len(drift_labels) > 0:
            msg.fail('Label drift detected on the following: '+', '.join(drift_labels))
        if len(drift_labels)==0 and len(warn_labels)==0:
            msg.good('Label distribution normal.')

    '''
    TODO: Implement these so that the model can be interrupted and restored
    '''

    def read_prediction_queue(self):
        pass

    def add_to_prediction_queue(self, instance_id, prediction, confidence):
        pass

    def get_from_prediction_queue(self, instance_id):
        pass

    def restore(self):
        pass
