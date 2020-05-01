from external_code.tornado.drift_detection.__init__ import *
from CDDM.CDDM import CDDM

DETECTOR_LIST = [
    # CDDM,
    ADWINChangeDetector,
    CUSUM,
    DDM,
    EDDM,
    FHDDM,
    FHDDMS,
    HDDM_A_test,
    HDDM_W_test,
    RDDM,
    PH,
    SeqDrift2ChangeDetector
]
