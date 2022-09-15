<!-- Badges -->

![Build Status](https://github.com/ornlneutronimaging/iMars3D/actions/workflows/ornl-prod.yml/badge.svg)
![Unittest Status](https://github.com/ornlneutronimaging/iMars3D/actions/workflows/unittest.yml/badge.svg?branch=next)
[![Documentation Status](https://readthedocs.org/projects/imars3d/badge/?version=latest)](https://imars3d.readthedocs.io/en/latest/?badge=latest)

<!-- End Badges -->

# iMars3D

A Python 3 Library used for
normalization, corrections, and reconstruction (using [tomopy](https://tomopy.readthedocs.io/en/latest/)) of the Neutron Imaging Beam Lines

# Install

## Install the Conda Environment

``` bash
conda env create -f conda_environment.yml
activate imars3d
```

### Install Dev Dependencies

If you plan on developing iMars3d itself then it is recommended you also install the dependencies is `conda_development.yml`

``` bash
conda env update --file conda_development.yml
```

## Install iMars3D

### Build a Wheel

``` bash
python -m build --no-isolation --wheel
```

### Install from Wheel

``` bash
python3 -m pip install dist/imars3d-*.whl
```

# Run

Import as you would any other library.

Refer to `path/to/unittests` for use/implementation examples.

Note: Explicit use examples to be included in docs at a later date.

# Test

Run unit tests with:

``` bash
python -m pytest tests/unit
```
