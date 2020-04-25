from bow_machine import BOWMachine
from Tornado import DDM
from cddm import CDDM
import unittest

class MedTextDetector:

    def __init__(
            self,
            label_set=[1,2,3,4], # the set of possible labels
            feature_dd, # feature drift detector
            label_dd, # label drift detector
            concept_dd=None, # concept drift detector
            real_dd=None, # real drift detector
            # cddm=False # whether to use CDDM or no
        ):

        self.bm = BOWMachine()

        self.label_set = label_set

        self.label_dd = label_dd
        self.label_dd_dict = { i:feature_dd() for i in label_set }
        self.labels = []
        self.label_val_dict = { i:[] for i in label_set }
        self.label_state_dict = { i:[] for i in label_set }

        self.feature_dd = feature_dd
        self.feature_dd_dict = {}
        self.feature_vals = {}


        self.concept_dd = concept_dd
        self.real_dd = real_dd

        self.labels = []
        self.predictions = []

        # self.concept_detector = None
        # self.virt_drift_detector = None

        # Each instance/label/prediction has a timestamp (ts)
        # associated with it.
        # EDIT: wait this doesn't make sense
        # self.instance_ts_list = []
        # self.label_ts_list = []
        # self.prediction_ts_list = []

    def add_training_docs(self, training_docs):

        train_data = self.bm.convert_train_data(strings)

        for feature in train_data.columns:
            this_feature_dd = feature_dd()
            for i in range(len(train_data)):
                value = train_data.loc[i, feature]
                this_feature_dd.update(value)
            self.feature_dd_dict[feature] = this_feature_dd

    def add_training_label(self, training_labels):
        for label_i in training_label:
            for label in self.label_set:
                outcome = label_i == label
                detector = self.label_dd_dict[label_i]
                self.detect_drift(detector, outcome)


    def add_label_prediction(self, prediction_dict, prediction):

        for label in self.label_set:
            outcome = label_i == label
            detector = label_dict[label_i]
            self.detect_drift(detector, outcome)

    def add_training_predictions(self, training_predictions):

        pass

    def add_instance(self, instance, instance_ts=None):

        # if instance_ts == None:
        #     instance_ts = self.instance_ts_list[-1]+1

        instance_data = self.bm.convert_online(strings)
        for col in instance_data.columns:
            self.label_detectors[col].do_something()

    def detect_drift(self, detector, val, prob=None):
        if prob:
            warning_status, drift_status = detector.detect(val, prob)
        else:
            warning_status, drift_status = detector.detect(val)
        return warning_status, drift_status

    def detect_concept_drift(self, i):
        label_i = self.labels[i]
        prediction_i = self.predictions[i]
        prediction_status = label_i == predictino_i
        return self.detect_drift(self.concept_dd, prediction_status)

    def add_label(self, label, instance_ts=None):

        # if instance_ts == None:
        #     instance_ts = self.label_ts_list[-1]+1

        detector.detect(prediction_status)
        i = len(self.labels)
        self.detect_concept_drift()

        pass

    def add_prediction(self, label, prob, instance_ts=None):

        # if instance_ts == None:
        #     instance_ts = self.prediction_ts_list[-1]+1


        pass
