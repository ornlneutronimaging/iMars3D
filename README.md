<!-- Badges -->

[![Build Status](https://github.com/ornlneutronimaging/iMars3D/actions/workflows/actions.yml/badge.svg?branch=next)](https://github.com/ornlneutronimaging/iMars3D/actions/workflows/actions.yml?query=branch?next)
[![Documentation Status](https://readthedocs.org/projects/imars3d/badge/?version=latest)](https://imars3d.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/ornlneutronimaging/iMars3D/branch/next/graph/badge.svg)](https://codecov.io/gh/ornlneutronimaging/iMars3D/tree/next)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/6650/badge)](https://bestpractices.coreinfrastructure.org/projects/6650)

<!-- End Badges -->

# iMars3D

A Python 3 Library used for
normalization, corrections, and reconstruction (using [tomopy](https://tomopy.readthedocs.io/en/latest/)) of the Neutron Imaging Beam Lines

# Install

The suggested method for installing imars3d is to create a new environment and install the package from https://anaconda.org/neutronimaging/imars3d.

# Run

Import as you would any other library.

Refer to `path/to/unittests` for use/implementation examples.

Note: Explicit use examples to be included in docs at a later date.

# Develop

## Install Developer Dependencies

If you plan on developing iMars3d itself then it is recommended you create a new conda environment using the `environment.yml`.

```sh
conda env create
activate imars3d
playwright install
```
The last command configures [playwright](https://playwright.dev/python/docs/intro) for running the unit tests.


## Test Data

The test data (currently 5GB) is stored in a second git repository [imars3d-data](https://code.ornl.gov/sns-hfir-scse/infrastructure/test-data/imars3d-data) which uses git-lfs.
To use it, first install git-lfs, then setup the git-submodule
```sh
git submodule init
git submodule update
```


## Running Tests

Run the tests with:

```sh
python -m pytest tests
```
The system is configured to produce coverage reports using the `--cov` flag.
