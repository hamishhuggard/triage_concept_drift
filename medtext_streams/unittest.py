
import unittest

from bow_machine import BOWMachine
from mimic_generator import MIMIC, MIMIC_NEGATE, MIMIC_UNDERSAMPLE, MIMIC_OVERSAMPLE
from medtext_detector import MedTextDetector

class TestMedTextStuff(unittest.TestCase):

    def test_cdddm(self):
        self.assertTrue(True)
        self.assertEqual(2, 1+1)

    def test_bow_machine(self):
        pass

    def test_medtext_detector(self):
        '''
        How can you test this thing?
        - basic functionality: inputting and outputting the right types without error
        - making sure it detects drifts within some time period
        -
        '''
        mtd = MedTextDetector()
        mtd.add_training_docs()
        mtd.add_training_label()
        mtd.add_training_predictions()

if __name__ == '__main__':
    unittest.main()
