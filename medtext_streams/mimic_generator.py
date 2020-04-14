import pandas as pd
import random
from sklearn.tree import DecisionTreeClassifier
from numpy.random import randint

class MIMIC:

    '''
    When creating a synthetic MIMIC-based dataset, this object
    contains a synthetic concept.
    '''

    MIMIC_DATA = None

    @staticmethod
    def get_mimic_data():
        # Load MIMIC data if it hasn't been already.
        if MIMIC.MIMIC_DATA == None:
            MIMIC.MIMIC_DATA = pd.read_csv(path_to_csv)
        return MIMIC.MIMIC_DATA

    def __init__(self, concept_length=20000, transition_length=50,
        noise_rate=0.1, n_priorities=4, n_concepts=5, random_seed=None):

        if random_seed==None:
            random_seed=random.randint(1000000)

        self.__INSTANCES_NUM = 5 * concept_length
        self.__CONCEPT_LENGTH = concept_length
        self.__NUM_DRIFTS = n_concepts - 1
        self.__W = transition_length
        self.__RECORDS = []
        self.__N_PRIORITIES = n_priorities
        self.__N_CONCEPTS = n_concepts

        self.__RANDOM_SEED = random_seed
        random.seed(self.__RANDOM_SEED)
        self.__NOISE_LOCATIONS = random.sample(range(0, self.__INSTANCES_NUM), int(self.__INSTANCES_NUM * noise_rate))

        print("You are going to generate a " + self.get_class_name() + " data stream containing " +
              str(self.__INSTANCES_NUM) + " instances, and " + str(self.__NUM_DRIFTS) + " concept drifts; " + "\n\r" +
              "where they appear at every " + str(self.__CONCEPT_LENGTH) + " instances.")

    @staticmethod
    def get_class_name():
        return 'MIMIC'

    def generate_concept(self, n_random_labels=20):
        concept = DecisionTreeClassifier()
        rand_labels = randint(1, self.__N_PRIORITIES+1, size=n_random_labels)
        concept.fit(data.iloc[:n_random_labels, :], rand_labels)
        return concept

    def generate(self, output_path="MIMIC"):

        random.seed(self.__RANDOM_SEED)

        # [1] CREATING CONCEPTS
        features_df = self.__FEATURES_DF = MIMIC.get_mimic_data().sample(self.__INSTANCES_NUM)
        concepts = self.__CONCEPTS = [ self.generate_concept() for i in n_concepts ]

        # [2] CREATING RECORDS
        for i in range(0, self.__NUM_INSTANCES):
            context_id = int(i / self.__CONCEPT_LENGTH)
            record = self.create_record(i, context_id)
            self.__RECORDS.append(list(record))

        # [3] TRANSITION
        for i in range(1, self.__NUM_DRIFTS + 1):
            transition = []
            for j in range(0, self.__W):
                instance_index = i * self.__CONEPT_LENGTH + j
                if random.random() < Transition.sigmoid(j, self.__W):
                    concept = self.__CONCEPTS[i-1]
                else:
                    concept = self.__CONCEPTS[i]
                record = self.create_record(instance_index, concept)
                transition.append(list(record))
            starting_index = i * self.__CONCEPT_LENGTH
            ending_index = starting_index + self.__W
            self.__RECORDS[starting_index: ending_index] = transition

        # [4] ADDING NOISE
        if len(self.__NOISE_LOCATIONS) != 0:
            self.add_noise()

        self.write_to_arff(output_path + ".arff")

    def create_record(self, i, dist_id):
        # i is the index of the instance in the features_df
        # dist_id is the concept index
        features = features_df.iloc[i, :]
        concept = self.__CONCEPTS[dist_id]
        label = concept.predict(features)
        return features + [label]

    def add_noise(self):
        for i in range(0, len(self.__NOISE_LOCATIONS)):
            noise_spot = self.__NOISE_LOCATIONS[i]
            c = self.__RECORDS[noise_spot][2]
            rand_add = random.randint(1, self.__N_PRIORITIES)
            self.__RECORDS[noise_spot][2] = (c+rand_add)%5

    def write_to_arff(self, output_path):
        arff_writer = open(output_path, "w")
        arff_writer.write("@relation MIMIC" + "\n")
        arff_writer.write("@attribute x real" + "\n" +
                          "@attribute y real" + "\n" +
                          "@attribute class {p,n}" + "\n\n")
        arff_writer.write("@data" + "\n")
        for i in range(0, len(self.__RECORDS)):
            arff_writer.write(str("%0.3f" % self.__RECORDS[i][0]) + "," +
                              str("%0.3f" % self.__RECORDS[i][1]) + "," +
                              self.__RECORDS[i][2] + "\n")
        arff_writer.close()
        print("You can find the generated files in " + output_path + "!")


class MIMIC_FEATURE_DRIFT:
    def __init__(self):
        pass
