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

        self.feature_dd = feature_dd
        self.label_dd = label_dd

        self.feature_dd_dict = {}
        self.label_dd_dict = {}

        self.concept_dd = concept_dd
        self.real_dd = real_dd

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
        pass

    def add_training_predictions(self, training_predictions):
        pass

    def add_instance(self, instance, instance_ts=None):

        # if instance_ts == None:
        #     instance_ts = self.instance_ts_list[-1]+1

        instance_data = self.bm.convert_online(strings)
        for col in instance_data.columns:
            self.label_detectors[col].do_something()

    def add_label(self, label, instance_ts=None):

        # if instance_ts == None:
        #     instance_ts = self.label_ts_list[-1]+1

        pass

    def add_prediction(self, label, instance_ts=None):

        # if instance_ts == None:
        #     instance_ts = self.prediction_ts_list[-1]+1


        pass
