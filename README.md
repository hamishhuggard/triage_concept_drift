# Triage Concept Drift

A package for detecting concept drift in medical referrals triage.

## A Primer On Drift

This section has been moved to [primer.ipynb](primer.ipynb) because github doesn't like Latex in READMEs.

It gives an introduction to the vocabulary used throughout.

## Instructions

### Environment

Step 1. Clone the package.
```
(base)$ git clone https://github.com/precisiondrivenhealth/triage_drift_detector.git
```

Step 2. Build the conda environment.
```
(base)$ cd triage_drift_detector
(base)$ conda env create -f=env.yml
```

Step 3. Activate the environment.
```
(base)$ conda activate triage_drift_env
```

Step 4. (Optional) If you want to use this environment in any notebooks, you will need to have `nb_conda_kernels` installed in the base environment. This will be necessary, for example, if you want to run [demo.ipynb](demo.ipynb).
```
(triage_drift_env)$ conda deactivate
(base)$ conda install nb_conda_kernels
```

### Drift Detector Usage

Step 1. Write a function to specify what should happen to messages signalling that drift has occurred.
```
>>> def send_drift_signal(signal):
  ...
```

Step 2. Specify a directory that the state of the drift detector should be recorded in.
This allows the drift detector to be restored if it is interrupted, and also allows the dash app to visualise the history of the detector.
```
>>> write_dir = './data/demo'
```

Step 3. Create a `MultiDriftDetector` object.
```
>>> detector = triage_detector.triage_detector.MultiDriftDetector(
    write_dir = write_dir,
    drift_action = display_message
)
```

Step 4. Specify the set of features and labels in the data stream
```
>>> detector.set_features(['Feature0', 'Feature1', ...])
>>> detector.set_labels(['Priority0', 'Priority1', ...])
```

Step 5. When a new instance (referral document) arrives, register it with the drift detector
```
>>> detector.add_instance([value1, value2, ...], id=...)
```

Step 6. When the model makes a new prediction, register it with the drift detector
```
>>> detector.add_prediction([softmax1, softmax2, ...], id=...)
```

Step 7. When a new ground-truth label (i.e., clinician triage label) arrives, register it with the drift detector
```
>>> detector.add_label(labelN, id=...)
```

Note that all these registration steps require an instance id.
This is so that the detector can keep track of which labels match with which predictions and which features.
This is necessary to track real drift.

For each of the registration steps, there is also an optional `description` argument
```
>>> detector.add_instance(labelN, id=..., description="...")
```
This is added to the hover-text of this data point in the graphical interface.

A detailed illustration of `MultiDriftDetector` usage is given in [demo.ipynb](demo.ipynb).

### Graphic Interface

After the drift detector has run, you can visualise the evolution of the data stream using the dash app.
The app is run as follows, where the argument is the directory that the drift detector was writing its status to.
```
(triage_drift_env)$ python drift_viewer/app.py data/demo
```
Unfortunately, this isn't working right now because I introduced a bug which I haven't been able to fix.

## TODO

 * Implement code in `MultiDriftDetector` for restoring from interrupt.
 * Fix dash app. Nevermind callback logic for now.
 * Differentiate concept drift detector from real drift detector?
 * In README, describe the contents of the repository
 * In README, talk about the choice of underlying drift detector.

<!--

## The Contents of this Repo



### MediTornado

A fork of the Tornado framework with the following additions:
 * An implementation of the CDDM algorithm
 * Data stream generators for medical data based on the MIMIC-III dataset
Note that this is a git [submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules) with its own repository.

## Conda cheatsheet

This is for my own benefit.

Create an environment with
```conda create --name <envname> python=<version> <optional dependencies>
```
And then remove it with
```
conda remove --name <envname> --all
```
Instal packages with
```
(envname)> conda install <package>
```
or
```
(envname)> pip install <package>
```
See a list of all packages with
```
conda list
```
Update the environment yaml with
```
conda env export > env.yml
```
Restore environment with
```
conda env create -f=env.yml
```
To use a conda environment in jupyter notebooks/labs, first install `nb_conda_kernels` in the base environment
```
(base)$ conda install -c conda-forge nb_conda_kernels
```
Then install `ipykernel` in the target environment
```
$ conda activate cenv
(cenv)$ conda install ipykernel
(cenv)$ conda deactivate
```
-->
