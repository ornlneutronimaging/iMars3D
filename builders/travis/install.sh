#!/bin/bash

set -e

export GIT_FULL_HASH=`git rev-parse HEAD`

if [ ${USE_CACHE} == "yes" ] ; then
    source activate testenv
else
    # install dependencies
    conda config --set always_yes true
    conda update conda
    conda config --add channels conda-forge
    conda create -n testenv python=$TRAVIS_PYTHON_VERSION
    conda install -n testenv pip pytest
    conda install -n testenv numpy
    conda install -n testenv scipy
    conda install -n testenv matplotlib
    conda install -n testenv astropy mpich mpi4py
    conda install -n testenv pyyaml
    conda install -n testenv -c dgursoy tomopy=0.1.15
    # conda install -n testenv -c scikit-xray xraylib lmfit=0.8.3 netcdf4 # install from scikit-xray channel
    conda install -n testenv psutil scikit-image
    conda install -n testenv -c neutrons ipywe
    conda install -n testenv -c conda-forge zeromq=4.2.1   # Jan 10, 2018. conda-forge: pyzmq 16.0.2 not compatible with latest zeromq 4.2.3
    source activate testenv
    pip install progressbar2
    pip install awscli
    # pip install coveralls
    # pip install codecov
fi

# install imars3d
# python setup.py install
