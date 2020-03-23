# Triage Concept Drift

Code produced by Hamish Huggard for his Master's Degree in computer science at UoA.

## Experiments



## Dash App



## MediTornado

A fork of the Tornado framework with the following additions:
 * An implementation of the CDDM algorithm
 * Data stream generators for medical data based on the MIMIC-III dataset
 *


conda = virtualenv + pip
if you have conda you don't need virtualenv, but you still need docker

> conda create --name <envname> python=<version> <optional dependencies>

> conda remove --name <envname> --all

(envname)> conda install <package>

(envname)> pip install <package>

Jupyter

In addition, installing ipykernel in an environment adds a new listing in the Kernels dropdown menu of Jupyter notebooks, extending reproducible environments to notebooks. As of Anaconda 4.1, nbextensions were added, adding extensions to notebooks more easily.

Reliability

In my experience, conda is faster and more reliable at installing large libraries such as numpy and pandas. Moreover, if you wish to transfer your the preserved state of an environment, you can do so by sharing or cloning an env.

conda list
gives all installed packages

REPRODUCING ENVIRONMENT

conda env create -f=env.yml

When you make changes to your environment, run an export before you add/commit:

conda env export > env.yml



Using conda environment in jupyter labs/notebook

https://stackoverflow.com/questions/53004311/how-to-add-conda-environment-to-jupyter-lab

A solution using nb_conda_kernels. First, install it in your base environment :

(base)$ conda install -c conda-forge nb_conda_kernels
Then in order to get a kernel for the conda_env cenv :

$ conda activate cenv
(cenv)$ conda install ipykernel
(cenv)$ conda deactivate
You will get a new kernel named Python [conda env:cenv] in your next run of jupyter lab / jupyter notebook
