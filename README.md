[![Build Status](https://travis-ci.org/ornlneutronimaging/iMars3D.svg?branch=master)](https://travis-ci.org/ornlneutronimaging/iMars3D) 

# iMars3D
Normalization, corrections, and reconstruction (using [tomopy](https://tomopy.readthedocs.io/en/latest/)) for the Neutron Imaging Beam Lines

Reconstruction of a CT scan:

```
>>> from imars3d.CT import CT
>>> ct = CT("/path/to/mydata")
>>> ct.recon()
```

# Installation under a conda environment

Install dependencies:
```
$ conda config --add channels conda-forge
$ conda install pytest pyyaml numpy scipy matplotlib astropy mpi4py psutil scikit-image
$ conda install -c dgursoy tomopy=0.1.15
$ conda install -c conda-forge dxchange
$ conda install -c conda-forge progressbar2
```

If running the jupyter interface, install more dependencies:

```
$ conda install -c neutrons ipywe
```

To install imars3d itself,

```
$ cd /path/to/imars3d; python setup.py install
```

# Conda environment for development of iMars3D and ipywe:

Using `mamba` instead of `conda`.  
First create the environment and install iMars3D dependencies, except for `ipywe`:  
```bash
mamba create --name imars3d python=3.8
conda activate imars3d
mamba install pytest pyyaml numpy scipy matplotlib astropy mpi4py mpich psutil scikit-image tomopy dxchange progressbar2
```
Install `ipywe` dependencies with this [requirements.txt](https://github.com/ornlneutronimaging/iMars3D/files/7338852/requirements.txt)
 file.
```bash
mamba install --file requirements.txt
```
Install `ipywe` in development mode, but before have `npm` installed.
```bash
sudo apt install npm
cd /home/jbq/repositories/scikit-beam/ipywe
python setup.py develop
```
Install `iMars3D` in development mode
```bash
cd /home/jbq/repositories/ornlneutronimaging/iMars3D
python setup.py develop
```

# Configuration
See tests/imars3d/imars3d.conf for an exampmle.
