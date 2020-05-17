# Triage Concept Drift

A package for detecting concept drift in medical referrals triage.

## A Primer On Drift

*Drift* is a change in the distribution of a data stream. A stream $z_1,z_2,\dots,z_n$ is said to experience drift when
$$
P_t(z) \ne P_{t'}(z)
$$
for some $t$ and $t'$.

*Concept drift* is any change in the joint distribution of features and labels. That is,
$$
P_t(x,y) \ne P_{t'}(x,y).
$$
However, simply learning that concept drift has occurred is not very helpful.
This package therefore separately detects three kinds of concept drift.

First, there is *feature drift*, which is a drift in the feature space:
$$
P_t(x) \ne P_{t'}(x).
$$

Second, there is *label drift*, which is a drift in the label space:
$$
P_t(y) \ne P_{t'}(y).
$$

Third, there is *real drift*, which is a drift in conditional distribution of labels on features:
$$
P_t(y|x) \ne P_{t'}(y|x)
$$
Most of the time it is only real drift that requires retraining.

## Instructions

### Setup

Step 1. Clone the package.
```
git clone https://github.com/precisiondrivenhealth/triage_drift_detector.git
```

Step 2. Build the conda environment.
```
cd triage_drift_detector
conda env create -f=env.yml
```

Step 3. Activate the environment.
```
conda activate triage_drift_env
```

### Drift Detector Usage

Step 1. Write a function to specify what should happen to messages signalling that drift has occurred.
```
def send_drift_signal(signal):
  pass
```

Step 2. Specify a directory that the state of the drift detector should be recorded in.
This allows the drift detector to be restored if it is interrupted, and also allows the dash app to visualise the history of the detector.
```
write_dir = './data/demo'
```

Step 3. Create a `MultiDriftDetector` object.
```
detector = MultiDriftDetector(
    write_dir = write_dir,
    drift_action = display_message
)
```

Step 4. Specify the set of features and labels in the data stream
```
detector.set_features(['Feature0', 'Feature1', ...])
detector.set_labels(['Priority0', 'Priority1', ...])
```

Step 5. When a new instance (referral document) arrives, register it with the drift detector
```
detector.add_instance([value1, value2, ...], id=...)
```

Step 6. When the model makes a new prediction, register it with the drift detector
```
detector.add_instance([softmax1, softmax2, ...], id=...)
```

Step 7. When a new ground-truth label (i.e., clinician triage label) arrives, register it with the drift detector
```
detector.add_instance(labelN, id=...)
```

Note that all these registration steps require an instance id.
This is so that the detector can keep track of which labels match with which predictions and which features.
This is necessary to track real drift.

For each of the registration steps, there is also an optional `description` argument
```
detector.add_instance(labelN, id=..., description="...")
```
This is added to the hover-text of this data point in the graphical interface.

A detailed illustration of `MultiDriftDetector` usage is given in [demo.ipynb](demo.ipynb).

Note that in order to use the `traige_drift_env` environment in the notebook, you will need to have `nb_conda_kernels` installed in the base environment:
```
conda deactivate
conda install nb_conda_kernels
```

### Graphic Interface


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
