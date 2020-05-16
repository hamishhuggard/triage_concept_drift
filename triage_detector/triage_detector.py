# from bow_machine import BOWMachine

# I don't know how to do this properly
import sys
import os
tornado_path = os.path.abspath('./tornado_med')
sys.path.insert(0, tornado_path)
from tornado_med.drift_detection.__init__ import *

from collections import defaultdict
# from data_stream import DataStream
import os
from wasabi import color, Printer
import numpy as np

class DataStream:

    color_messages = True

    message_colors = {
        'NORMAL': 'green',
        'WARNING': 'yellow',
        'DRIFT': 'red'
    }

    def __init__(self, detector, drift_action=print, name='unknown'):
        self.drift_action = drift_action
        self.detector = detector
        self.status = 'NORMAL'
        self.name = name

    def add_value(self, value, conf=None):
        # conf is confidence. This is for CDDM.

        # Determine if this data stream has drifted
        if conf:
            warning_status, drift_status = self.detector.detect(value, conf)
        else:
            warning_status, drift_status = self.detector.detect(value)

        if drift_status:
            new_status = 'DRIFT'
        elif warning_status:
            new_status = 'WARNING'
        else:
            new_status = 'NORMAL'

        if new_status=='NORMAL' and self.status=='DRIFT':
            # Once a drift is detected you don't want to go back to undetected
            new_status = 'DRIFT'

        # If the status has changed then send do a drift action
        if new_status != self.status:
            message = f'The status of {self.name} has changed to '
            if DataStream.color_messages:
                bg_color = DataStream.message_colors[new_status]
                message += color(new_status, fg="white", bg=bg_color, bold=True)
            else:
                message += new_status
            self.drift_action(message)
            self.status = new_status

        return new_status

    def get_status(self):
        return self.status

class MultiDriftDetector:

    # These are the drift detection algorithms to detect:
    feature_dd=RDDM#HDDM_A_test # feature drift
    label_dd=RDDM#HDDM_A_test # label drift
    concept_dd=RDDM#HDDM_A_test # concept drift

    # And these are the kwargs for instantiating the drift detectors.
    feature_dd_kwargs={}
    label_dd_kwargs={}
    concept_dd_kwargs={}

    def __init__(
            self,
            write_dir,
            drift_action=print
        ):

        self.write_dir = write_dir
        self.drift_action = drift_action

        # Set up the directories
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
            detector = MultiDriftDetector.concept_dd(**MultiDriftDetector.concept_dd_kwargs),
            name = 'Concept Drift'
        )

        self.prediction_queue = {}

    def init_file(self, fpath):
        with open(fpath, 'w') as f:
            f.write('value,status,description\n')

    def append_file(self, fpath, value, status, description):
        with open(fpath, 'a') as f:
            f.write(f'{value},{status},"{description}"\n')

    def set_features(self, feature_names):

        self.feature_names = feature_names

        # Set up a DataStream object to monitor each feature.
        self.feature_streams = {
            feature_name: DataStream(
                drift_action = self.drift_action,
                detector = MultiDriftDetector.feature_dd(**MultiDriftDetector.feature_dd_kwargs),
                name = feature_name
            ) for feature_name in feature_names
        }

        # Create the header for the feature files
        for feature_name in feature_names:
            feature_path = os.path.join(self.feature_dir, feature_name+'.csv')
            self.init_file(feature_path)

    def set_labels(self, label_names):

        self.label_names = label_names

        # Set up a DataStream object to monitor each label value.
        self.label_streams = {
            label_name: DataStream(
                drift_action = self.drift_action,
                detector = MultiDriftDetector.label_dd(**MultiDriftDetector.label_dd_kwargs),
                name = label_name
            ) for label_name in label_names
        }

        # Create the header for the feature files
        for label_name in label_names:
            label_path = os.path.join(self.predictions_dir, label_name+'.csv')
            self.init_file(label_path)

    def add_instance(self, instance, instance_id, description=''):

        for feature_name, value in zip(self.feature_names, instance):
            feature_stream = self.feature_streams[feature_name]
            status = feature_stream.add_value(value)
            feature_path = os.path.join(self.feature_dir, feature_name+'.csv')
            self.append_file(feature_path, value, status, description)

    def add_label(self, label, instance_id, description=''):

        # retrieve from queue with confidence
        (prediction, confidence) = self.prediction_queue[instance_id]

        value = label != prediction

        if MultiDriftDetector.concept_dd.DETECTOR_NAME == 'CDDM':
            status = self.loss_stream.add_value(value, confidence)
        else:
            status = self.loss_stream.add_value(value)

        self.append_file(self.loss_file, value, status, description)

    def add_prediction(self, prediction, instance_id, description=''):

        label = self.label_names[np.argmax(prediction)]
        confidence = np.max(prediction)

        for label_name in self.label_names:
            value = label_name == label
            label_stream = self.label_streams[label_name]
            status = label_stream.add_value(value)
            label_path = os.path.join(self.predictions_dir, label_name+'.csv')
            self.append_file(label_path, value, status, description)

        self.prediction_queue[instance_id] = (label, confidence)

    def get_status(self):

        msg = Printer()

        # Display concept drift status
        concept_status = self.loss_stream.get_status()
        if concept_status == 'DRIFT':
            msg.fail('Concept drift detected.')
        elif concept_status == 'WARNING':
            msg.warn('Concept drift suspected.')
        else:
            msg.good('No concept drift detected.')

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
            msg.warn('Feature drift suspected on the following: '+','.join(warn_features))
        if len(drift_features) > 0:
            msg.fail('Feature drift detected on the following: '+','.join(drift_features))
        if len(drift_features)==0 and len(warn_features)==0:
            msg.good('No feature drift detected.')

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
            msg.warn('Label drift suspected on the following: '+','.join(warn_labels))
        if len(drift_labels) > 0:
            msg.fail('Label drift detected on the following: '+','.join(drift_labels))
        if len(drift_labels)==0 and len(warn_labels)==0:
            msg.good('No label drift detected.')

    '''
    Implement these so that the model can be interrupted and restored
    '''

    def read_prediction_queue(self):
        pass

    def add_to_prediction_queue(self, instance_id, prediction, confidence):
        pass

    def get_from_prediction_queue(self, instance_id):
        pass

    def restore(self):
        pass


class TriageDetector0:

    '''
    The order in which label_predictions arrive is the canonical order of these
    the labels. Each label_prediction is associated with an id, which allows
    them to be matched up with true_labels, in the event that the latter arrives
    in a different order than the former.

    Example usage:
    >>> md = MedTextDetector(
        label_set=[1,2,3,4],
        feature_dd=DDM,
        label_dd=DDM,
        concept_dd=CDDM
    )
    >>> md.add_training_docs(list_of_referral_docs)
    >>> md.add_training_labels(list_of_referral_triage_labels)
    >>> md.
    # When a new referral document arrives
    >>> md.add_new_doc()
    # When a
    '''

    def __init__(
            self,

            label_set=[1,2,3,4], # the set of possible labels
            index_instances=False,
            dir_name=None,
            drift_action=print,

            feature_dd=None,
            true_label_dd=None,
            pred_label_dd=None,
            concept_dd=None,

            feature_dd_kwargs={},
            true_label_dd_kwargs={},
            pred_label_dd_kwargs={},
            concept_dd_kwargs={},
        ):
        '''
        Args:
        - label_set: a list of the possible priority labels
        - index_instances: bool indicating whether each instance is indexed.
            This is because predicted_labels and true_labels can arrive
            asynchronously, so indices may be needed to match predicted_labels
            with true_labels. If set to False, then predicted_labels are assumed
            to arrive in the same order as true_labels.
        - feature_dd: class of the feature drift detector
        - true_label_dd: class of the label drift detector
        - concept_dd: class of the concept drift detector
        - x_dd_kwargs for x in {feature,true_label,pred_label,concept}:
            kwargs for the instantiation of any of the x drift detector.
            That is, each drift detector will be constructed as x_dd(**x_dd_kwargs).
        '''


        # Label stream stuff
        self.label_set = label_set
        self.pred_label_stream_dict = {
            i:DataStream('Label={i}', label_dd(**pred_label_dd_kwargs))
            for i in label_set
        }

        self.true_label_stream_dict = {
            i:DataStream('Label={i}', label_dd(**true_label_dd_kwargs))
            for i in label_set
        }
        # Label queues for handling label asynchronicities
        self.true_label_queue = []
        self.pred_label_queue = []
        self.model_conf_queue = []
        self.EXPECT_MODEL_CONF = true_label_dd==CDDM
        self.label_id_queue = []

        # Feature stream stuff
        self.bm = BOWMachine()
        self.feature_dd = feature_dd
        self.feature_dd_kwargs = feature_dd_kwargs
        self.feature_stream_dict = {}

        # Loss stream stuff
        self.loss_stream = DataStream('Loss', concept_dd(**concept_dd_kwargs))

        # Initialize the directories where data will be stored in CSV format
        self.ROOT_DIR = os.path.abspath(dir_name)
        self.paths = {}
        for sub_dir in ['features', 'pred_labels', 'true_labels', 'loss']:
            dir_path = os.path.join(self.ROOT_DIR, sub_dir)
            self.paths[sub_dir] = {}
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            # Create the files where the values and drift statuses will be recorded
            for fname in ['values.csv', 'statuses.csv']:
                file_path = os.path.join(dir_path, fname)
                self.paths[sub_dir][fname] = file_path
                with open(file_path, 'w') as f:
                    # Create the headers for the csv files
                    if sub_dir.endswith('labels'):
                        header = ','.join([str(i) for i in label_set]) + '\n'
                    elif sub_dir == 'loss':
                        header = 'loss\n'
                    else:
                        header = ''
                    f.write(header)
        annotations_path = os.path.join(self.ROOT_DIR, 'annotations.txt')
        with open(annotations_path, 'w'):
            pass
        self.paths['annotations'] = annotations_path
        self.ANNOTATIONS_SEP = '='*20 + '\n'

    def update_label_streams(self, stream_dicts, label, conf):

        for label_i in self.label_set:
            stream_dicts[label_i].add_value(label==label_i, conf)

    def add_predicted_label(self, label, id, conf=None):

        if (conf!=None) and (self.EXPECT_MODEL_CONF==False):
            raise ValueError('Model confidence provided when none expected.')
        if (conf==None) and (self.EXPECT_MODEL_CONF==True):
            raise ValueError('No model confidence provided when expected.')

        self.pred_label_queue.append(label)
        self.model_conf_queue.append(conf)
        self.label_id_queue.append(id)
        self.true_label_queue.append(None) # the true_label_queue should be the same length as the pred_label_queue

        self.update_label_streams(self.pred_label_stream_dict, label)

    def add_true_label(self, label, id):

        # Match this true label with its corresponding predicted label
        # by finding the latter with the same ID.
        def find_id_index(id):
            for i, id_i in enumerate(self.label_id_queue):
                if id_i == id:
                    return id_i
            raise ValueError(f'Tried to add true label {label} with ID {id},' + \
                ' but there is no predicted label with the same ID')

        index = find_id_index(id)
        self.true_label_queue[index] = label

        # Flush out complete pairs of predicted and true labels
        while len(self.true_label_queue) > 0:
            if self.true_label_queue[0] != None:
                true_label = self.true_label_queue.pop(0)
                pred_label = self.pred_label_queue.pop(0)
                model_conf = self.model_conf_queue.pop(0)
                id = self.label_id_queue.pop(0)
                loss = true_label == pred_label
                self.update_label_streams(self.true_label_stream_dict, true_label)
                self.loss_stream.add_value(loss, model_conf)
            else:
                break

    def add_training_docs(self, training_docs):

        train_data = self.bm.convert_train_data(training_docs)

        for feature in train_data.columns:

            new_feature_dd = self.feature_dd(**self.feature_dd_kwargs)
            feature_name = f'Feature: "{feature}"'
            feature_stream = DataStream(feature_name, new_feature_dd)
            feature_stream.set_training_period(True)

            for i in range(len(train_data)):
                value = train_data.loc[i, feature]
                feature_stream.add_value(value)
            self.feature_stream_dict[feature] = feature_stream

            feature_stream.set_training_period(False)

    def add_doc(self, doc):

        doc_data = self.bm.convert_online([doc])

        for feature in doc_data.columns:
            value = train_data.loc[i, 0]
            feature_stream = self.feature_stream_dict[feature].add_value(value)



    def print_statuses(self):
        status_str = ''

        # Concept drift
        drift_status = self.loss_stream.get_current_status()
        if drift_status == 'Warning':
            status_str += 'Concept drift warning has been triggered.\n'
        if drift_status == 'Drift':
            status_str += 'Concept drift has been detected.\n'

        # Read off the drift statuses from a dictionary of streams
        def stream_dict_status_str(steam_dict, stream_type):

            status_str = ''

            status_dict = defaultdict([])
            for key, stream in stream_dict.items():
                key_status = stream.get_current_status()
                status_dict[key_status].append(key)

            if len(status_dict['Warning']) > 0:
                status_str += 'Drift warning has been triggered for '
                status_str += stream_type
                status_str += ' with values '
                status_str += ', '.join(sorted(status_dict['Warning']))
                status_str += '\n'
            if len(status_dict['Drift']) > 0:
                status_str += 'Drift has been detected for '
                status_str += stream_type
                status_str += ' with values '
                status_str += ', '.join(sorted(status_dict['Drift']))
                status_str += '\n'

            # If string is non-empty, then prettify it
            if len(status_str) > 0:
                status_str = stream_type.upper() + '\n' + status_str + '\n'

            return status_str

        # Label drift
        status_str += stream_dict_status_str(self.true_label_stream_dict, 'true labels')
        status_str += stream_dict_status_str(self.pred_label_stream_dict, 'predicted labels')
        status_str += stream_dict_status_str(self.feature_stream_dict, 'features')

        if len(status_str) == 0:
            status_str = 'No drifts detected.'

        print(status_str)

'''
TODO:
- what happens with training true labels or predictions?
'''
