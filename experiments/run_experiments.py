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

## Instantiate the datastreams ##

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
        n_drifts = eval(f'stream_obj_i._{stream_name}__NUM_DRIFTS') # double underscore name mangling
        stream_drift_locs = [ (i+1)*concept_length for i in range(n_drifts) ]
        drift_locations[stream_name] = stream_drift_locs
    
    return drift_locations

### Run single experimental trial ###

def run_trial(stream_path, target_dir, drift_points, pairs):
    
    # for example, stream_path='./benchmark_data/circles/circles_0.arff'
    
    # 1. Creating a project
    stream_name = os.path.splitext(os.path.basename(stream_path))[0]
    project = Project(target_dir, stream_name)
    
    # 2. Loading an arff file
    labels, attributes, stream_records = ARFFReader.read(stream_path)
    attributes_scheme = AttributeScheme.get_scheme(attributes)

    # 4. Creating a color set for plotting results
    colors = [Color.Indigo[1], Color.Blue[1], Color.Green[1], Color.Lime[1], Color.Yellow[1],
          Color.Amber[1], Color.Orange[1], Color.Red[1], Color.Purple[1], Color.Pink[1],
          Color.Indigo[2], Color.Blue[2], Color.Green[2], Color.Lime[2], Color.Yellow[2],
          Color.Amber[2], Color.Orange[2], Color.Red[2], Color.Purple[2], Color.Pink[2],
          Color.Indigo[3], Color.Blue[3], Color.Green[3], Color.Lime[3], Color.Yellow[3],
          Color.Amber[3], Color.Orange[3], Color.Red[3], Color.Purple[3], Color.Pink[3]][:len(pairs)]

    # 5. Defining actual locations of drifts, acceptance delay interval, and vector of weights
    actual_drift_points = drift_points
    drift_acceptance_interval = 250
#     w_vec = [1]*len(drift_points)
    w_vec = [1, 1, 1, 1, 1, 1]

    # 6. Creating a Prequential Evaluation Process
    pairs = [ [pair[0](labels, attributes_scheme[pair[1]]), copy(pair[2])] for pair in pairs ]
    prequential = PrequentialMultiPairs(pairs, attributes, attributes_scheme,
                                        actual_drift_points, drift_acceptance_interval,
                                        w_vec, project, color_set=colors, legend_param=False)

    prequential.run(stream_records, 1)
    
    
### All all experimental trials ###

def run_trials(stream_dir, target_dir, drift_loc_dic, pairs):
    
    for stream_path in glob(f'./{stream_dir}/**/*.arff'):
        
        stream_path = os.path.abspath(stream_path)
        target_path = os.path.abspath(target_dir)
        
        _, ext = os.path.splitext(stream_path)
        _, trial = os.path.split(_)
        _, dataset = os.path.split(_)
        
        target_path = os.path.join(target_path, dataset)
        
        run_trial(stream_path, target_path, drift_loc_dic[dataset], pairs)
        
### Parse single trial ###

def parse_trial(trial_path):
    
    path = os.path.abspath(trial_path)
    dataset_name, ext = os.path.splitext(os.path.basename(trial_path))
    
    with open(path) as f:
        lines = f.read().split('\n')
    headers = lines[0].rstrip(']').lstrip('[')
    headers = [ header.lstrip() for header in headers.split(',') ]
    results = pd.DataFrame(columns=headers)
    i = 1
    for line in lines[1:]:
        fields = line.split('\t')
        if fields==['']:
            continue
        results.loc[i, :] = fields
        i += 1
        
    results['Dataset'] = dataset_name
        
    # Parse "Drift Detector Stats"
    total_delay = []
    tp = []
    location_of_last_detection = []
    fp, fn = [], []
    for i in range(len(results)):
        temp = eval(results.loc[i+1, 'Drift Detector Stats'])
        tdi, [lldi, tpi], fpi, fni = temp
        total_delay.append(tdi)
        tp.append(tpi)
        location_of_last_detection.append(lldi)
        fp.append(fpi)
        fn.append(fni)
    results['Total Delay'] = total_delay
    results['TP'] = tp
    results['FN'] = fn
    results['FP'] = fp
    
    for i in ['Total Delay', 'TP', 'FN', 'FP', 'Avg. Total Memory', 'Avg. Total Runtime', 'Avg. Error-rate', 'Total Delay']:
        results[i] = results[i].astype('float')
    
    # Split up name
    models = []
    detectors = []
    for i in range(len(results)):
        name = results.loc[i+1, 'Name']
        n_match = re.match('([\w\s]+) \+ ([\w\.]+)', name)
        models.append( n_match.group(1) )
        detectors.append( n_match.group(2) )
    results['Model'] = models
    results['Detector'] = detectors
    
    # Get wanted columns in right order
    results = results[['Dataset', 'Detector', 'Model', 'TP', 'FN', 'FP', 'Avg. Error-rate', 'Avg. Total Memory', 'Avg. Total Runtime', 'Total Delay']]
    results.columns = ['Dataset', 'Detector', 'Model', 'TP', 'FN', 'FP', 'Err-rate', 'Memory', 'Runtime', 'Total Delay']
        
    return results

### Parse all trials ###

def parse_trials(experiment_dir):
    results = pd.DataFrame(columns=['Dataset', 'Detector', 'Model', 'TP', 'FN', 'FP', 'Err-rate', 'Memory', 'Runtime', 'Total Delay'])
    for path in glob(f'./{experiment_dir}/*/*/*/*.txt'):#f'./{experiment_dir}/*/*/*.txt'):
        results = results.append(parse_trial(path))
    return results

## All together now ##

# def run_tornado(detectors, data_streams, n_trials, data_dir, results_dir, concept_length=20000):
#     create_datastreams(data_dir, data_streams, n_trials, concept_length)

def condense_table(results):
    
    results2 = pd.DataFrame()
    
    ##########################################
    ###### Create the experiment column ######
    ##########################################
    
    def get_ds_name(str_):
        # get dataset name
        return re.match(r'([a-z]+).*', str_).group(1).upper()
    ds_names = results['Dataset'].apply(get_ds_name)
    
    det_names_map = {'HDDM.A.test': r'HDDM_A', 'CDDM': 'CDDM', 'RDDM': 'RDDM'}
    det_names = results['Detector'].map(det_names_map)
    
    model_names_map = {'NAIVE BAYES': 'NB', 'PERCEPTRON': 'PR'}
    model_names = results['Model'].map(model_names_map)
    
    exp_names = ds_names + '+' + det_names + '+' + model_names
    results2['Experiment'] = exp_names

    # Copy over other metrics
    for i in ['Memory', 'Runtime', 'Total Delay', 'Prec', 'Rec', 'Mean Delay', 'TPR']:
        results2[i] = results[i].astype('float')
        
    ##########################################
    ###### Mean and Standard Deviation  ######
    ##########################################
    
    mean_results = pd.DataFrame(columns=results2.columns, 
                               index=results2['Experiment'].unique())
    
    for exp in results2['Experiment'].unique():
        
        this_exp = results2[ results2['Experiment']==exp ]
        
        for col in mean_results.columns:
            
            if col=='Experiment':
                mean_results.loc[exp, col] = exp
                continue
            
            col_vals = this_exp[col]
            
            mean = np.nanmean(col_vals)
            std = np.nanstd(col_vals)
            
            entry = f'{mean:.2f} ({std:.2f})' if not np.isnan(mean) else '- (-)'
            mean_results.loc[exp, col] = entry
            
    mean_results.drop(columns='Experiment', inplace=True)
        
    return mean_results

def extend_metrics(results):
    tp = results['TP'].astype('float')
    fp = results['FP'].astype('float')
    fn = results['FN'].astype('float')
    prec = ( tp / (tp + fp) )
    prec = prec.map(lambda x: x if np.isfinite(x) else np.nan)
    rec = ( tp / (tp + fn) )
    results['Prec'] = prec
    results['Rec'] = rec
    n_positives = results['TP']+results['FN']
    total_delay = results['Total Delay'].astype('float')
    results['Mean Delay'] = total_delay / n_positives.astype('float')
    results['TPR'] = (tp+1) / (total_delay+1)
#     results['FPR'] = (fp+1) / total_timesteps
    return results