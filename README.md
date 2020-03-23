# Triage Concept Drift

Code produced by Hamish Huggard for his Master's Degree in computer science at UoA.

Reproduce the Conda environment I used with
```
conda env create -f=env.yml
```

### Conda cheatsheet

This is for my own benefit.

What is conda?
 * conda = virtualenv + pip
 * If you have conda you don't need virtualenv, but you still need docker

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

## Experiments

A bunch of notebooks and csvs which record the outcomes of experiments.

## Dash App

A GUI for interacting with concept drift detection systems built using Dash.

## MediTornado

A fork of the Tornado framework with the following additions:
 * An implementation of the CDDM algorithm
 * Data stream generators for medical data based on the MIMIC-III dataset
Note that this is a git [submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules) with its own repository.
