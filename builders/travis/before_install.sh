#!/bin/bash

set -e

# check
df -h
free

if [ ${USE_CACHE} == "no" ] ; then
    # get MC
    if [ ${TRAVIS_PYTHON_VERSION:0:1} == "2" ]; then
	wget http://repo.continuum.io/miniconda/Miniconda-3.5.5-Linux-x86_64.sh -O miniconda.sh;
    else
	wget http://repo.continuum.io/miniconda/Miniconda3-3.5.5-Linux-x86_64.sh -O miniconda.sh;
    fi

    # install MC
    chmod +x miniconda.sh
    ./miniconda.sh -b -p /home/travis/mc
fi
