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
    conda create -n testenv python=3.6
    conda activate testenv
    conda install -n testenv -c dgursoy -c neutrons pytest psutil pyyaml scipy matplotlib astropy mpi4py scikit-image tomopy ipywe zeromq progressbar2 awscli

    # conda install -n testenv pip pytest psutil pyyaml
    # conda install -n testenv numpy=1.14 scipy matplotlib astropy mpich mpi4py scikit-image 
    # conda install -n testenv -c dgursoy tomopy=0.1.15 numpy=1.14  # Sep 30, 2018. weird conda error
    # conda install -n testenv -c scikit-xray xraylib lmfit=0.8.3 netcdf4 # install from scikit-xray channel
    # conda install -n testenv -c neutrons ipywe numpy=1.14 # Sep 30, 2018. weird conda error
    # conda install -n testenv -c conda-forge zeromq=4.2.1 numpy=1.14  # Jan 10, 2018. conda-forge: pyzmq 16.0.2 not compatible with latest zeromq 4.2.3
    # source activate testenv
    # conda install progressbar2 awscli
    # pip install coveralls
    # pip install codecov
fi

# install imars3d
# python setup.py install
