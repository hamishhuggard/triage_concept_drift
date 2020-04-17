from bow_machine import BOWMachine
from Tornado import DDM
from cddm import CDDM

class MedTextDetector:

    def __init__(
            self,
            feature_dd,
            label_dd, # label drift detector
            concept_dd=DDM, # concept drift detector
            real_dd=CDDM # real drift detector
        ):
        self.bm = BOWMachine()
        self.feature_detectors = {}
        self.label_detectors = {}
        self.cdrift_detector = None
        self.virt_drift_detector = None

    def train(self, train_data):
        self.bm.convert_train_data(strings)

    def add_instance(self, instance, instance_id):
        instance_data = self.bm.convert_train_data(strings)
        for col in instance_data.columns:
            self.label_detectors[col].do_something()

    def add_label(self, label, instance_id):
        pass

    def add_prediction(self, label, instance_id):
        pass
