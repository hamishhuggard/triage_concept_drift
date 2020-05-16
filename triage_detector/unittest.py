
import unittest

from bow_machine import BOWMachine
from mimic_generator import MIMIC, MIMIC_NEGATE, MIMIC_UNDERSAMPLE, MIMIC_OVERSAMPLE
from medtext_detector import MedTextDetector

class TestMedTextStuff(unittest.TestCase):

    def test_cdddm(self):
        self.assertTrue(True)
        self.assertEqual(2, 1+1)

    def test_medtext_detector(self):
        '''
        How can you test this thing?
        - basic functionality: inputting and outputting the right types without error
        - making sure it detects drifts within some time period
        -
        '''
        #########################
        ## INITIALIZE DETECTOR ##
        #########################

        # Instantiate the detector
        mtd = MedTextDetector(
            label_set=[1,2,3], # This stream has three triage labels
            feature_dd=DDM, # DDM is the drift detector for detected changes in feature distribution
            label_dd=DDM, # DDM is the drift detector for detected changes in label distribution
            concept_dd=CDDM, # CDDM is the drift detector for detected changes in P(y|x)
            drift_signal_output=print, # When a drift is detected, the status is printed
        )
        # Add the referral documents from the training data
        mtd.add_training_docs([
            'patient has plague',
            'patient is a werewolf',
            'this patient also has plague',
            'plague and werewolf'
        ])
        # Add the triage labels from the training data
        mtd.add_training_label([
            1,
            2,
            1,
            3
        ])
        # Add the model predictions from the training data
        mtd.add_training_predictions([
            [0.5, 0.4, 0.1],
            [0.2, 0.6, 0.2],
            [0.4, 0.3, 0.3],
            [0.1, 0.5, 0.4]
        ])

        ################
        ## DEPLOYMENT ##
        ################

        # Some new referral documents arrive
        mtd.add_new_doc('another plague patient', id=0)
        mtd.add_new_doc('another werewolf patient', id=1)

        # The model predicts the labels for these documents
        mtd.add_prediction([0.5, 0.4, 0.1], id=0)
        mtd.add_prediction([0.2, 0.6, 0.2], id=1)

        # A clinician provides a triage label for the second patient.
        # Note this is this is not in the order that the referral docs arrived.
        mtd.add_true_label(2, id=1)

        # Another referral document arrives
        mtd.add_new_doc('plague werewolf again', id=2)
        mtd.add_prediction([0.1, 0.5, 0.4], id=2)

        # And so on...

        ##################
        ## DRIFT STATUS ##
        ##################

        self.assertEqual(mtd.get_drift_status(), 'Normal')


if __name__ == '__main__':
    unittest.main()
