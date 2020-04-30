class DataStream:

    '''
    DataStream encapsulates a stream of data, including:
    - Adding new values to the data stream
    - Monitoring the stream with a drift detector
    - Sending warning or drift signals if a drift is detected or suspected

    Data streams may include:
    - Feature values (for detecting feature drift)
    - Label values, either predicted labels or true labels (for detecting label drift)
    - Loss values (for detecting concept drift)
    '''

    def __init__(self, name, detector):
        self.detector = detector
        self.values = []
        self.statuses = []
        self.SEND_SIGNALS = True

    def turn_on_signals(self):
        '''
        Use this function to stop the DataStream from sending warning and drift
        signals. Useful for when the datastream is loading instances from the
        training data.
        '''
        self.SEND_SIGNALS = False

    def turn_off_signals(self):
        '''
        Use this function to start the DataStream sending warning and drift
        signals. Useful for when the datastream has finished loading instances
        from the training data and is now deployed.
        '''
        self.SEND_SIGNALS = False

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

        return status

    def send_warning_signal(self):
        self.send_signal('Drift warning in {self.name}')

    def send_drift_signal(self):
        self.send_signal(f'Drift detected in {self.name}')

    def send_signal(self, signal):
        '''
        Action to be taken when a drift is detected or suspected for this DataStream.
        By default the signal is simply printed.
        '''
        if self.SEND_SIGNALS == True:
            print(signal)

    def get_current_status(self):
        '''
        Get the current status of the data stream. Is it normal, is drift
        detected, or has a drift warning been activated?
        '''
        return self.statuses[-1]
