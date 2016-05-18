[![Build Status](https://travis-ci.org/ornlneutronimaging/iMars3D.svg?branch=master)](https://travis-ci.org/ornlneutronimaging/iMars3D) 

# iMars3D
Normalization, corrections, and reconstruction for the Neutron Imaging Beam Lines

Reconstruction of a CT scan:

```
>>> from imars3d.CT import CT
>>> ct = CT("/path/to/mydata")
>>> ct.recon()
```
