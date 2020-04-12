import pandas as pd
import random
from sklearn.tree import DecisionTreeClassifier
from numpy.random import randint

class MimicDataWrapper:

    '''
    This wraps the MIMIC-III data and spawns the machine readable
    '''

    def __init__(self, path_to_csv):
        self.data = pd.read_csv(path_to_csv)

    def get_full_feature_stream(self):
        return self.data

    def get_mimic_feature_stream(self):
        pass

    def get_data_shuffle(self, n):
        return self.sample(n)

class MIMIC:

    '''
    When creating a synthetic MIMIC-based dataset, this object
    contains a synthetic concept.
    '''


    def __init__(self, concept_length=20000, transition_length=50,
        noise_rate=0.1, n_priorities=4, random_seed=None):

        if random_seed==None:
            random_seed=random.randint(1000000)

        self.__INSTANCES_NUM = 5 * concept_length
        self.__CONCEPT_LENGTH = concept_length
        self.__NUM_DRIFTS = 4
        self.__W = transition_length
        self.__RECORDS = []
        self.__N_PRIORITIES = n_priorities

        self.__RANDOM_SEED = random_seed
        random.seed(self.__RANDOM_SEED)
        self.__NOISE_LOCATIONS = random.sample(range(0, self.__INSTANCES_NUM), int(self.__INSTANCES_NUM * noise_rate))

        print("You are going to generate a " + self.get_class_name() + " data stream containing " +
              str(self.__INSTANCES_NUM) + " instances, and " + str(self.__NUM_DRIFTS) + " concept drifts; " + "\n\r" +
              "where they appear at every " + str(self.__CONCEPT_LENGTH) + " instances.")

    @staticmethod
    def get_class_name():
        return 'MIMIC'

    def generate(self, output_path="MIMIC"):

        random.seed(self.__RANDOM_SEED)

        # [1] CREATING RECORDS
        for i in range(0, self.__INSTANCES_NUM):
            concept_sec = int(i / self.__CONCEPT_LENGTH)
            dist_id = int(concept_sec % 2)
            record = self.create_record(dist_id)
            self.__RECORDS.append(list(record))

        # [2] TRANSITION
        for i in range(1, self.__NUM_DRIFTS + 1):
            transition = []
            if (i % 2) == 1:
                for j in range(0, self.__W):
                    if random.random() < Transition.sigmoid(j, self.__W):
                        record = self.create_record(1)
                    else:
                        record = self.create_record(0)
                    transition.append(list(record))
            else:
                for j in range(0, self.__W):
                    if random.random() < Transition.sigmoid(j, self.__W):
                        record = self.create_record(0)
                    else:
                        record = self.create_record(1)
                    transition.append(list(record))
            starting_index = i * self.__CONCEPT_LENGTH
            ending_index = starting_index + self.__W
            self.__RECORDS[starting_index: ending_index] = transition

        # [3] ADDING NOISE
        if len(self.__NOISE_LOCATIONS) != 0:
            self.add_noise()

        self.write_to_arff(output_path + ".arff")

    def create_record(self, dist_id):
        x, y, c = self.create_attribute_values()
        if random.random() < 0.5:
            while c != 'p':
                x, y, c = self.create_attribute_values()
        else:
            while c != 'n':
                x, y, c = self.create_attribute_values()
        if dist_id == 1:
            c = 'n' if c == 'p' else 'p'
        return x, y, c

    def add_noise(self):
        for i in range(0, len(self.__NOISE_LOCATIONS)):
            noise_spot = self.__NOISE_LOCATIONS[i]
            c = self.__RECORDS[noise_spot][2]
            rand_add = random.randint(1, self.__N_PRIORITIES)
            self.__RECORDS[noise_spot][2] = (c+rand_add)%5

    def write_to_arff(self, output_path):
        arff_writer = open(output_path, "w")
        arff_writer.write("@relation SINE1" + "\n")
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


    n_priority_levels = 4

    def __init__(self, mimic_stream):
        self.mimic_stream = mimic_stream

    def add_labels(self, n_random_items):
        '''

        '''

        # Create concept
        self.model = dtree = DecisionTreeClassifier()
        rand_labels = randint(1, n_priority_levels+1, size=n_random_labels)
        dtree.fit(data.iloc[:n_random_labels, :], rand_labels)

        #

class MIMIC_FEATURE_DRIFT
