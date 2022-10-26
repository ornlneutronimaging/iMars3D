"""iMars3D: a Python package for neutron imaging and tomography reconstruction."""
import logging

logging.getLogger("imars3d").setLevel(logging.INFO)
try:
    from ._version import __version__  # noqa: F401
except ImportError:
    __version__ = "unknown"
