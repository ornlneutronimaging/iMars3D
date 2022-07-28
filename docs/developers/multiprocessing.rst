Parallelization via multiprocessing
===================================

Background
----------

In neutron imaging, the input data is often a 3D array.
Depending on the axis of observation, the data can be interpreted as either a
stack of radiographs (rotation angle) or a stack of sinograms (row number).
Most of the filters in iMars3D is intended to adjust one single 2D image, therefore
the filtering of a 3D array can be and should be parallelized over the axis that is
not of interest.
For instance, a typical radiograph from neutron imaging can have some contamination
from stray gamma radiation, resulting in nearly/over saturated pixels randomly spreading
over the image.
Since the identification and correction of these gamma contamination does not depend on
the rotation angle, the corresponding filter can be parallelized over the rotation angle
axis so as to improve the overall performance.


Usage of multiprocessing and real-time feedback via progress-bar
----------------------------------------------------------------

The modern Python have native support for parallelization, via either the
`multithreading <https://docs.python.org/3/library/threading.html>`_ or
the `multiprocessing <https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing>`_ module.
A high-level encapsulation package,
`concurrent.futures <https://docs.python.org/3/library/concurrent.futures.html#module-concurrent.futures>`_,
also becomes available in Python 3.2, which significantly simplifies the implementation of parallelization.
Generally speaking, multithreading is useful for non-CPU intensive tasks as it does not entirely
bypass the GIL (Global Interpreter Lock).
In the case of iMars3D, multiprocessing is selected as most of the filters are computationally
intensive.
Furthermore, the shared memory array is used to avoid sending pickled Numpy array via messaging between processes,
which further improves the overall performance.

Another common request from users is the ability to see the progress of the filtering process, regardless
of the backend implementation.
This was originally achieved via a customized progress-bar in the version of iMars3D 1.0 where each status
from MPI process is reported and counted explicitly.
However, the newer version of iMars3D (v2.0) opts to use an established progress-bar library,
`tqdm <https://tqdm.github.io/>`_.
Furthermore, ``tqdm`` also provides a high-level wrapper for both multiprocessing
(`process_map <https://tqdm.github.io/docs/contrib.concurrent/#process_map>`_) and
multithreading (`thread_map <https://tqdm.github.io/docs/contrib.concurrent/#thread_map>`_).


Usage of shared memory model
----------------------------

Starting from version 3.8, Python provides a native support for using shared memory within multiprocessing.
The general steps consist of the following:

- declare a shared memory instance with specified size.
- create a shared memory array and copy the data from regular Numpy array to the shared memory array.
- processing the data via multiprocessing.
- close the shared memory array.
- unlink the shared memory array.
- close the shared memory instance.
- unlink the shared memory instance.

This explicit memory management is somewhat un-pythonic, and it is possible to simplify the syntax by using
the shared memory manager as a context manager, which will take care of close and unlink the shared memory
instance and arrays automatically.


Examples
--------

Here is a simple Python script that demonstrate how the shared memory model and the progress-bar can be integrated
within the same functions.

.. code-block:: python

    #!/usr/bin/env python3

    from multiprocessing.managers import SharedMemoryManager
    from tqdm.contrib.concurrent import process_map
    from functools import partial
    import numpy as np

    def example_func(np_array, i):
        return np.power(np_array[i, :, :], 2)

    def mproc_wrapper(func, np_array):
        """
        This is a wrapper to use multiprocessing with
            - progress bar via tqdm
            - shared memory to reduce footprint
        """
        with SharedMemoryManager() as smm:
            # create the shared memory
            shm = smm.SharedMemory(np_array.nbytes)
            # create a numpy array point to the shared memory
            shm_np_array = np.ndarray(
                np_array.shape,
                dtype=np_array.dtype,
                buffer=shm.buf,
            )
            # copy the data to the shared memory
            np.copyto(shm_np_array, np_array)
            #
            rst = process_map(
                partial(func, shm_np_array),
                range(np_array.shape[0]),
                max_workers=4,
            )
        return rst

    if __name__ == "__main__":
        # make fake large image stack
        data = np.random.random(36 * 512 * 512).reshape(36, 512, 512)
        # test the wrapper
        result = mproc_wrapper(example_func, data)
        # verify
        np.testing.assert_equal(
            np.power(data, 2),
            result,
        )


Known issues
------------

Here are several known issues regarding the parallelization in iMars3D:

- Filters that are thin wrapper around ``tomopy`` functions do not have progress bar.
    - An upstream update is needed to bring the support of ``map_process`` to ``tomopy`` natively.
- Currently iMars3D is assuming that all sub-processes have access to the same physical RAM.
    - Support for distributed memory is planned and will be added in the future.
