import random
import numpy as np

class BERNOULLI:

    def __init__(self, concepts, concept_length=25000, transition_length=500, random_seed=10):
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

        self.write_to_arff(output_path + ".arff")

    def create_record(self, concept):
        PX1, PY1X0, PY1X1 = concept # that is, P(X=1), P(Y=1|X=0), P(Y=1|X=1)
        x = np.random.choice(2, p=[1-PX1, PX1])
        PY1 = PY1X0 if x==0 else PY1X1
        y = x = np.random.choice(2, p=[1-PY1, PY1])
        return x, y

    def write_to_arff(self, output_path):
        arff_writer = open(output_path, "w")
        arff_writer.write("@relation BERNOULLI" + "\n")
        arff_writer.write("@attribute x {0,1}" + "\n" +
                          "@attribute y {0,1}" + "\n\n")
        arff_writer.write("@data" + "\n")

        for i in range(0, len(self.__RECORDS)):
            arff_writer.write(str(self.__RECORDS[i][0]) + "," +
                              str(self.__RECORDS[i][1]) + "\n")
        arff_writer.close()
        print("You can find the generated files in " + output_path + "!")



class BERNOULLI_BASIC(BERNOULLI):

    def __init__(self, noise=0.1, PX1=0.5 repeats=1, concept_length=25000, transition_length=500, random_seed=10):
        c1 = [1-noise, noise]
        c2 = [noise, 1-noise]
        concepts = [(PX1, *c1), (PX1, *c2)] * repeats
        super().__init__(concepts, concept_length, transition_length, random_seed)

class BERNOULLI_FP(BERNOULLI):

    def __init__(self, dPX1=0.1, noise=0.1, repeats=1, concept_length=25000, transition_length=500, random_seed=10):
        c1 = [1-noise, noise]
        concepts = [(0.5+dPX1, *c1), (0.5-dPX1, *c1)] * repeats
        super().__init__(concepts, concept_length, transition_length, random_seed)


class BERNOULLI_FN(BERNOULLI):

    def __init__(self, noise=0.1, d_noise=0.1, repeats=1, concept_length=25000, transition_length=500, random_seed=10):
        dPX1 = noise / (2*d_noise)
        c1 = [1-noise, noise]
        c2 = [1-noise-d_noise, noise+d_noise]
        concepts = [(0.5+dPX1, *c1), (0.5-dPX1, *c2)] * repeats
        super().__init__(concepts, concept_length, transition_length, random_seed)


class BERNOULLI_TRICKY(BERNOULLI):

    def __init__(self, epsilon=0.1, concept_length=25000, transition_length=500, random_seed=10):
        concepts = [(0.5-epsilon, 0.9, 0.4), (0.5+epsilon, 0.9, 0.4)]
        super().__init__(concepts, concept_length, transition_length, random_seed)
