from bow_machine import BOWMachine
from Tornado import DDM
from cddm import CDDM
import unittest
from collections import defaultdict

class DataStream:

    def __init__(self, name, detector):
        self.detector = detector
        self.values = []
        self.statuses = []
        self.TRAINING_PERIOD = False

    def set_training_period(self, value):
        '''
        If the data stream hasn't loaded all of the training data values, then
        we should have self.set_training_period(True), and no drift signals will
        be emitted. When actually observing data online, then we should have
        self.set_training_period(False).
        '''
        self.TRAINING_PERIOD = value

    def add_value(self, value, confidence=None):
        '''
        Update this datastream with a new value.
        Args:
        - value: the value to be added
        - confidence: in case this is a prediction stream and CDDM is the
            drift detector, this is the confidence of the model.
        '''

        if prob: # for CDDM
            warning_status, drift_status = self.detector.detect(value, prob)
        else:
            warning_status, drift_status = self.detector.detect(value)

        status = 'Normal'
        if warning_status:
            status = 'Warning'
            self.send_warning_signal()
        if drift_status:
            status = 'Drift'
            self.send_drift_signal()

        self.values.append(value)
        self.statuses.append(status)

    def send_warning_signal(self):
        if self.training_period == False:
            print('Drift warning in', self.name)

    def send_drift_signal(self):
        if self.training_period == False:
            print('Drift detected in', self.name)



class MedTextDetector:

    '''
    The order in which label_predictions arrive is the canonical order of these
    the labels. Each label_prediction is associated with an id, which allows
    them to be matched up with true_labels, in the event that the latter arrives
    in a different order than the former.
    '''

    def __init__(
            self,

            label_set=[1,2,3,4], # the set of possible labels
            index_instances=False,

            feature_dd=None, # feature drift detector
            true_label_dd=None, # true label drift detector
            pred_label_dd=None, # predicted label drift detector
            concept_dd=None, # concept drift detector

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


'''
TODO:
- what happens with training true labels or predictions?
'''
