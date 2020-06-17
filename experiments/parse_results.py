import numpy as np
import pandas as pd
import os
import sys
import re
from glob import glob
import matplotlib.pyplot as plt
from copy import copy

from cd_diagrams import *
import scikit_posthocs as sp

##########################
### Parse single trial ###
##########################

def parse_trial(trial_path):

    path = os.path.abspath(trial_path)
#     dataset_name, ext = os.path.splitext(os.path.basename(trial_path))

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

    for i in [
        'Total Delay', 'TP', 'FN', 'FP', 'Avg. Total Memory',
        'Avg. Total Runtime', 'Avg. Error-rate', 'Total Delay'
    ]:
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
    results = results[[
        'Detector', 'Model', 'TP', 'FN', 'FP', 'Avg. Error-rate',
        'Avg. Total Memory', 'Avg. Total Runtime', 'Total Delay'
    ]]
    results.columns = [
        'Detector', 'Model', 'TP', 'FN', 'FP',
        'Err-rate', 'Memory', 'Runtime', 'Total Delay'
    ]

    return results

########################
### Parse all trials ###
########################

def parse_results(results_dir):
    results = results = pd.DataFrame(columns=[
        'Detector', 'Model', 'TP', 'FN', 'FP',
        'Err-rate', 'Memory', 'Runtime', 'Total Delay'
    ])
    for path in list(glob(f'{results_dir}/**/*.txt', recursive=True)):
        subresults = parse_trial(path)
        path_bits = path.split(os.sep)[1:-1]
        for i, bit in enumerate(path_bits):
            subresults[f'd{i}'] = bit
        results = results.append(subresults)
    return results

######################
### Extend metrics ###
######################

def extend_metrics(results):
    '''
    Create a modified version of the table results which
    additionally includes precision, recall, mean delay,
    true positive rate, and false positive rate.
    '''
    tp = results['TP'].astype('float')
    fp = results['FP'].astype('float')
    fn = results['FN'].astype('float')
    prec = ( tp / (tp + fp) )
    prec = prec.map(lambda x: x if np.isfinite(x) else np.nan)
    rec = ( tp / (tp + fn) )
    results['Precision'] = prec
    results['Recall'] = rec
    n_positives = results['TP']+results['FN']
    total_delay = results['Total Delay'].astype('float')
    results['Mean Delay'] = total_delay / n_positives.astype('float')
    # results['TPR'] = (tp+1) / (total_delay+1)
    # results['FPR'] = (fp+1) / total_timesteps
    return results

#######################
### Process results ###
#######################

def process_results(results, groupby='Detector', latex_path=None, fig_path=None,
        bold_best=False, alpha=0.05, one_fig=True, cd_diagram=True):
    '''
    args:
        results (dataframe): table of results.
        groupby (string, list of strings): the name of the column which groups values together
        path (string or None): the location to write the latex table to (if not None)
        bold_best (bool): should the best value in each column be bolded?
    '''
    full_results = results.drop(columns='dataset_name').groupby(groupby)#, as_index=False)
    results_summary = full_results.agg(lambda x: f'{np.mean(x):.2f} ({np.std(x):.2f})')

    ## Embolden the best values for each column ##
    results_means = full_results.mean()
    if bold_best:
        for col in results_means.columns:
            if col==groupby or col in groupby or col=='dataset_name':
                continue
            if col in ['Precision', 'Recall']:
                idxbf = results_means[col].idxmax()
            elif col in ['Err-rate', 'Memory', 'Runtime', 'Mean Delay']:
                idxbf = results_means[col].idxmin()
            else:
                raise ValueError(f"Is it good if {col} is high or low?")
            results_summary.loc[idxbf, col] = '{bf ' + results_summary.loc[idxbf, col] + '}'

    # Make table latex ready
    results_latex = results_summary.to_latex()#index=False)

    # replace ll...l align with lr...r align
    (l_start, l_fin) = re.search('l(l+)', results_latex).span()
    l_start += 1
    results_latex = results_latex[:l_start ] + 'r'*(l_fin-l_start) + results_latex[l_fin: ]

    ## Make names more readable ##
    before_after = {
        'Mean Delay': 'Mean Delay',
        'Memory': 'Memory (bytes)',
        'Runtime': 'Runtime (ms)',
        'Err-rate': 'Err-rate (\%)',
        'PageHinkley': 'PH',
        'NAIVE BAYES': 'NB',
        'PERCEPTRON': 'PR',
        'HOEFFDING TREE': 'HT',
        'LEDConceptDrift': 'LED',
        '\{bf ': '{\\fontseries{b}\\selectfont ',
        '\}': '}'
    }
    before_after.update({
        f'HDDM.{x}.test': f'HDDM$_{x}$' for x in 'AW'
    })
    # Replace underscores with spaces in mode names
    if 'Mode' in results.columns:
        before_after.update({
            x.replace('_', '\_'): ' '.join(x.split('_')).title() for x in results['Mode'].unique()
        })
        # print(before_after)
    for before, after in before_after.items():
        # if after != '}':
        #     after = after.rjust(len(before))
        results_latex = results_latex.replace(before, after)

    # Write the LaTeX table to disk
    if latex_path:
        with open(os.path.abspath(latex_path)+'.csv', 'w') as f:
            f.write(results_latex)
            print('Writing LaTeX table to', latex_path)

    ## CD DIAGRAMS ##
    if not cd_diagram:
        return results_latex
    if one_fig:
        nfigs = len(results_summary.columns)# if results not in ['Detector', 'dataset_name'])
        nfigs = nfigs+1 if nfigs%2==0 else nfigs
        nrows = nfigs // 2
        ncols = 2
        fig_i = 1
        width=9
        height=3
        fig = plt.figure(figsize=(width*2+1, height*nrows+1))
        fig.set_facecolor('white')
    # change names of detectors according to before_after dictionary
    results.loc[:, 'Detector'] = results.Detector.map(before_after).fillna(results['Detector'])
    for col in results_means.columns:

        # Figure out if the plot should be reversed or not
        if col==groupby or col in groupby or col=='dataset_name':
            continue
        if col in ['Precision', 'Recall']:
            reverse=True
        elif col in ['Err-rate', 'Memory', 'Runtime', 'Mean Delay']:
            reverse=False
        else:
            raise ValueError(f"Is it good if {col} is high or low?")

        # Convert the column data into matrix form
        dets = results.Detector.unique()
        dsets = results.dataset_name.unique()
        data = []
        for dset in dsets:
            row = []
            for det in dets:
                # print(dset)
                x = list(results[(results['Detector']==det) & (results['dataset_name']==dset)][col])[0]
                row.append(x)
            data.append(row)
        data = np.array(data)

        # Perform Nemenyi-Friedman test
        nem = sp.posthoc_nemenyi_friedman(data)

        # Put p-values in a form that the cd-diagram code can use
        p_vals = []
        for i, det1 in enumerate(dets):
            for j, det2 in enumerate(dets[i+1: ]):
                p_val = nem[i][j+i+1]
                p_vals.append(( det1, det2, p_val, p_val<alpha ))

        # Set span of CD-diagram and compute average values or average rank
        lowv, highv = None, None
        if col in ['Precision', 'Recall']: # , 'Err-rate'
            lowv, highv = 0, 1
            average_vals = results.groupby('Detector').mean()[col]
            if col=='Err-rate':
                lowv, highv = 0, 100
        else:
            # Compute average rank
            average_vals = pd.DataFrame(columns=['Detector', col])
            for dset in results.dataset_name:
                results_i = results[ results['dataset_name']==dset ]
                # print(col)
                # print(results_i[['Detector', col]])
                results_i.loc[:, col] = results_i[col].rank(ascending=True)
                # print(results_i[['Detector', col]])
                average_vals = average_vals.append(results_i[['Detector', col]])
                # break
            # sys.exit()
            # print(col)
            # print(average_vals)
            average_vals = average_vals.groupby('Detector').mean()[col]
            # print(average_vals)


        # Put the average values in a form that the cd-diagram code can use
        average_vals = average_vals.sort_values()
        if reverse:
            average_vals = average_vals[::-1]
        # minv = average_vals.min()
        # maxv = average_vals.max()

        # Plot the cd diagram
        if one_fig:
            ax = fig.add_subplot(nrows, ncols, fig_i)
            fig_i += 1
        else:
            ax = None
        graph_ranks(
            average_vals.values,
            average_vals.keys(),
            p_vals,
            cd=None,
            reverse=reverse,
            textspace=1, labels=False,
            highv=highv, lowv=lowv,
            ax=ax,
            width=width,
            height=height,
            # highv = int(maxv + (maxv-minv)*0.1),
            # lowv = int(minv - (maxv-minv)*0.1)
        )
        font = {'family': 'sans-serif',
            'color':  'black',
            'weight': 'normal',
            'size': 22,
        }
        ax.set_title(col,fontdict=font, y=0.9, x=0.5)
        if not one_fig:
            # fig_path = os.path.abspath(path)+f"-{col.replace(' ', '_')}.pdf"
            plt.savefig(fig_path,bbox_inches='tight')

    if one_fig:
        # fig_path = os.path.abspath(path)+".pdf"
        # plt.show()
        print('Writing cd diagrams to', fig_path)
        plt.savefig(fig_path, bbox_inches='tight')

    return results_latex

    # title_things = ['Detector', 'Model', 'mode', 'datastream']
