
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
        pass

if __name__ == '__main__':
    unittest.main()
