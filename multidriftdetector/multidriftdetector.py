import sys
import os
from collections import defaultdict
import os
from wasabi import color, Printer
import numpy as np
from copy import copy
from multidriftdetector.datastream import DataStream
from tornado_mod.drift_detection.__init__ import *

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
            write_dir,
            drift_action=print
            drift_detector=HDDM_A_test,
            warning_confidence=0.01,
            drift_confidence=0.005,
        ):
        '''
        args:
        - write_dir: the directory to write the state of the detector
        - drift_action: the action to take if drift is detected
        - drift_detector: a SuperDetector object for detecting changes in a data stream
        - warning_confidence: the p-value of the no-drift hypothesis at which a drift warning is sent
        - drift_confidence: the p-value of the no-drift hypothesis at which a drift signal is sent
        '''

        # only hddm uses drift_confidence and warning_confidence
        # adwin, cusum, fhddm, fhddms, mddm, page_hinkey, seq_drift2 use delta

        self.write_dir = write_dir
        self.drift_action = drift_action
        self.drift_detector = drift_detector
        self.warning_confidence = warning_confidence
        self.drift_confidence = drift_confidence

        # Set up the directory for recording detector state
        root = self.root_dir = os.path.abspath(write_dir)
        fdir = self.feature_dir = os.path.join(root, 'features')
        pdir = self.predictions_dir = os.path.join(root, 'predictions')
        adir = self.accuracy_dir = os.path.join(root, 'accuracy')
        prec_dir = self.precision_dir = os.path.join(root, 'precision')
        rec_dir = self.recall_dir = os.path.join(root, 'recall')
        for xdir in [fdir, pdir, adir, prec_dir, rec_dir]:
            if not os.path.exists(xdir):
                os.makedirs(xdir)

        # Create the record of model loss
        self.loss_file = os.path.join(adir, 'accuracy.csv')
        with open(self.loss_file, 'w') as f:
            f.write('value,status,description\n')
        self.loss_stream = DataStream(
            drift_action = self.drift_action,
            detector = copy(MultiDriftDetector.concept_dd),
            name = 'Concept Drift',
            bidirectional=False # only detect increases in loss
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
