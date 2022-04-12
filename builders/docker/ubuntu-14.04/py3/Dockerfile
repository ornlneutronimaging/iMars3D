FROM ubuntu:14.04

MAINTAINER "Jiao Lin <linjiao@caltech.edu>"

LABEL Description="image prepared for buildindg iMars3D"

# use bash instead of sh
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# installation of basic software and dependencies
RUN apt-get update
#
# to install mini conda
RUN apt-get -qy install python wget

# install mini conda
RUN wget http://repo.continuum.io/miniconda/Miniconda-3.5.5-Linux-x86_64.sh -O miniconda.sh
RUN chmod +x miniconda.sh
RUN ./miniconda.sh -b -p /home/travis/mc
ENV PATH=/home/travis/mc/bin:$PATH

# install deps
RUN conda config --set always_yes true
RUN conda update conda
RUN conda install python=3.5
RUN conda install pip pytest
RUN conda install pyyaml numpy scipy matplotlib astropy
# RUN conda install -c scikit-xray xraylib lmfit=0.8.3 netcdf4 # install from scikit-xray channel
RUN pip install progressbar2

# get source
RUN apt-get -qy install git
RUN git clone https://github.com/ornlneutronimaging/iMars3D
WORKDIR iMars3D
# build and install
RUN python setup.py install


# test
RUN apt-get -qy install unzip
RUN python tests/getdata.py
RUN python tests/imars3d/signon.py

# make matplotlib happy
RUN apt-get -qy install libsm6 libxrender1 libfontconfig1
RUN apt-get -qy install libglib2.0-0

#
# RUN py.test
