from bow_machine import BOWMachine
from Tornado import DDM
from cddm import CDDM
from collections import defaultdict
from data_stream import DataStream
import os

# TODO: combine pred_label_dd and true_label_dd

class MedTextDetector:

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
            drift_signal_output=print,

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
