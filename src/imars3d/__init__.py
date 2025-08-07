"""iMars3D: a Python package for neutron imaging and tomography reconstruction."""

import logging

# Apply NumPy 2.0 compatibility patches for tomopy before importing backend modules
from .backend.util.tomopy_compat import apply_tomopy_numpy2_compat

apply_tomopy_numpy2_compat()

from .backend import corrections, dataio, diagnostics, morph, preparation, reconstruction  # noqa: F401

logging.getLogger("imars3d").setLevel(logging.INFO)
try:
    from ._version import __version__  # noqa: F401
except ImportError:
    __version__ = "unknown"
