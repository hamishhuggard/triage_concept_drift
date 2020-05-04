import random
import numpy as np

class BERNOULLI:

    def __init__(self, concepts, concept_length=25000, transition_length=500, noise_rate=0.1, random_seed=10):
        '''
        Each concept is specified by a triple of values (P(X=1), P(Y=1|X=0), P(Y=0|X=1))
        '''
        self.__CONCEPTS = concepts
        self.__INSTANCES_NUM = concept_length * len(self.__CONCEPTS)
        self.__CONCEPT_LENGTH = concept_length
        self.__NUM_DRIFTS = len(self.__CONCEPTS) - 1
        self.__W = transition_length
        self.__RECORDS = []

        self.__RANDOM_SEED = random_seed
        random.seed(self.__RANDOM_SEED)
        self.__NOISE_LOCATIONS = random.sample(range(0, self.__INSTANCES_NUM), int(self.__INSTANCES_NUM * noise_rate))

        print("You are going to generate a " + self.get_class_name() + " data stream containing " +
              str(self.__INSTANCES_NUM) + " instances, and " + str(self.__NUM_DRIFTS) + " concept drifts; " + "\n\r" +
              "where they appear at every " + str(self.__CONCEPT_LENGTH) + " instances.")

    @staticmethod
    def get_class_name():
        return BERNOULLI.__name__

    def generate(self, output_path="BERNOULLI"):

        random.seed(self.__RANDOM_SEED)

        # [1] CREATING RECORDS
        for i in range(0, self.__INSTANCES_NUM):
            concept_sec = int(i / self.__CONCEPT_LENGTH)
            record = self.create_record(self.__CONCEPTS[concept_sec])
            self.__RECORDS.append(list(record))

        # [2] TRANSITION
        for i in range(0, self.__NUM_DRIFTS):
            transition = []
            for j in range(0, self.__W):
                if random.random() < Transition.sigmoid(j, self.__W):
                    record = self.create_record(self.__CONCEPTS[i + 1])
                else:
                    record = self.create_record(self.__CONCEPTS[i])
                transition.append(list(record))
            starting_index = i * self.__CONCEPT_LENGTH
            ending_index = starting_index + self.__W
            self.__RECORDS[starting_index: ending_index] = transition

        # [3] ADDING NOISE
        if len(self.__NOISE_LOCATIONS) != 0:
            self.add_noise()

        self.write_to_arff(output_path + ".arff")

    def create_record(self, concept):
        PX1, PY1X0, PY1X1 = concept # that is, P(X=1), P(Y=1|X=0), P(Y=1|X=1)
        x = np.random.choice(2, p=[1-PX1, PX1])
        PY1 = PY1X0 if x==0 else PY1X1
        y = x = np.random.choice(2, p=[1-PY1, PY1])
        return x, y


class SquareStream:

    def __init__(self):
        pass
