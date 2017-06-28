[![Build Status](https://travis-ci.org/ornlneutronimaging/iMars3D.svg?branch=master)](https://travis-ci.org/ornlneutronimaging/iMars3D) 

# iMars3D
Normalization, corrections, and reconstruction for the Neutron Imaging Beam Lines

Reconstruction of a CT scan:

```
>>> from imars3d.CT import CT
>>> ct = CT("/path/to/mydata")
>>> ct.recon()
```

# Installation under a conda environment

Install dependencies:
```
$ conda install pytest pyyaml numpy scipy matplotlib astropy mpi4py psutil scikit-image
$ conda install -c dgursoy tomopy=0.1.15
$ pip install progressbar2
```

If running the jupyter interface, install more dependencies:

```
$ conda install ipywidgets
$ cd /path/to/ipywe; python setup.py install
```

To install imars3d itself,

```
$ cd /path/to/imars3d; python setup.py install
```
