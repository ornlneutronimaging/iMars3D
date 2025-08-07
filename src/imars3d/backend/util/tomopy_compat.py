"""
Compatibility patches for tomopy with NumPy 2.0.

This module patches tomopy functions that are incompatible with NumPy 2.0.
"""

import numpy as np


def apply_tomopy_numpy2_compat():
    """Apply monkey patches to tomopy for NumPy 2.0 compatibility."""
    # First, patch numpy.lib.index_tricks if needed (used by tomopy.misc.phantom)
    if not hasattr(np.lib, "index_tricks"):
        np.lib.index_tricks = np.lib._index_tricks_impl

    # Import tomopy after numpy patching
    try:
        import tomopy.util.dtype as tomopy_dtype

        # Patch the as_dtype function to use np.asarray instead of np.array with copy=False
        def patched_as_dtype(arr, dtype, copy=False):
            if not arr.dtype == dtype:
                # Use asarray which allows copies when needed (NumPy 2.0 compatible)
                if copy:
                    arr = np.array(arr, dtype=dtype, copy=True)
                else:
                    arr = np.asarray(arr, dtype=dtype)
            return arr

        # Patch the as_ndarray function to use np.asarray instead of np.array with copy=False
        def patched_as_ndarray(arr, dtype=None, copy=False):
            if not isinstance(arr, np.ndarray):
                # Use asarray which allows copies when needed (NumPy 2.0 compatible)
                if copy:
                    arr = np.array(arr, dtype=dtype, copy=True)
                else:
                    arr = np.asarray(arr, dtype=dtype)
            return arr

        tomopy_dtype.as_dtype = patched_as_dtype
        tomopy_dtype.as_ndarray = patched_as_ndarray

    except ImportError:
        # tomopy not installed, skip patching
        pass
