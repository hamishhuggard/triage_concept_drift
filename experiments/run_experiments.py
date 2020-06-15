import numpy as np
import pandas as pd
import os
import sys
import re
from glob import glob
import matplotlib.pyplot as plt
from copy import copy

tornado_path = os.path.abspath('./tornado')
sys.path.insert(0, tornado_path)

from data_structures.attribute_scheme import AttributeScheme
from filters.project_creator import Project
from graphic.hex_colors import Color
from streams.readers.arff_reader import ARFFReader
from tasks.prequential_learner_detector_pairs import PrequentialMultiPairs

#################################
## Instantiate the datastreams ##
#################################

def create_datastreams(path, stream_objects, n_trials=1, stream_kwargs={'concept_length':20000}):
    '''
    Instantiate n_copies instances of every stream generator in stream_objects.
    These instances are recorded as arffs under path.
    '''

    concept_length = stream_kwargs['concept_length']

    # dictionary to record the locations of the drifts for each stream
    drift_locations = {}

    for stream_obj in stream_objects:

        # give this stream its own directory for its data
        stream_name = stream_obj.get_class_name()
        stream_path = os.path.join(path, stream_name)
        if not os.path.exists(stream_path):
            os.makedirs(stream_path)

        # create n copies of the stream
        for i in range(n_trials):
            copy_path = os.path.join(stream_path, f'{stream_name}_{i}')
            stream_obj_i = stream_obj(random_seed=i, **stream_kwargs)
            stream_obj_i.generate(copy_path)

        # add entry to drift_locations
        stream_name_short = 'BERNOULLI' if stream_name.startswith('BERNOULLI') else stream_name
        n_drifts = eval(f'stream_obj_i._{stream_name_short}__NUM_DRIFTS') # double underscore name mangling
        stream_drift_locs = [ (i+1)*concept_length for i in range(n_drifts) ]
        drift_locations[stream_name] = stream_drift_locs

    return drift_locations

#####################################
### Run single experimental trial ###
#####################################

def run_trial(stream_path, target_dir, drift_points, pairs):

    # for example, stream_path='./benchmark_data/circles/circles_0.arff'

    # 1. Creating a project
    stream_name = os.path.splitext(os.path.basename(stream_path))[0]
    project = Project(target_dir, stream_name)

    # 2. Loading an arff file
    labels, attributes, stream_records = ARFFReader.read(stream_path)
    attributes_scheme = AttributeScheme.get_scheme(attributes)

    # 4. Creating a color set for plotting results
#     colors = [Color.Indigo[1], Color.Blue[1], Color.Green[1], Color.Lime[1], Color.Yellow[1],
#           Color.Amber[1], Color.Orange[1], Color.Red[1], Color.Purple[1], Color.Pink[1],
#           Color.Indigo[2], Color.Blue[2], Color.Green[2], Color.Lime[2], Color.Yellow[2],
#           Color.Amber[2], Color.Orange[2], Color.Red[2], Color.Purple[2], Color.Pink[2],
#           Color.Indigo[3], Color.Blue[3], Color.Green[3], Color.Lime[3], Color.Yellow[3],
#           Color.Amber[3], Color.Orange[3], Color.Red[3], Color.Purple[3], Color.Pink[3]][:len(pairs)]

    # 5. Defining actual locations of drifts, acceptance delay interval, and vector of weights
    actual_drift_points = drift_points
    drift_acceptance_interval = 250
    w_vec = [1, 1, 1, 1, 1, 1]

    # 6. Creating a Prequential Evaluation Process
    pairs = [ [pair[0](labels, attributes_scheme[pair[1]]), copy(pair[2])] for pair in pairs ]
    prequential = PrequentialMultiPairs(pairs, attributes, attributes_scheme,
                                        actual_drift_points, drift_acceptance_interval,
                                        w_vec, project, legend_param=False) # color_set=colors,

    prequential.run(stream_records, 1)

###################################
### All all experimental trials ###
###################################

def run_trials(stream_dir, target_dir, drift_loc_dic, pairs):

    for stream_path in glob(f'{stream_dir}/**/*.arff', recursive=True):

        stream_path = os.path.abspath(stream_path)
        target_path = os.path.abspath(target_dir)

        _, ext = os.path.splitext(stream_path)
        _, trial = os.path.split(_)
        _, dataset = os.path.split(_)

        target_path = os.path.join(target_path, dataset)

        run_trial(stream_path, target_path, drift_loc_dic[dataset], pairs)
