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


Usage of multiprocessing
------------------------

Show how multiprocessing is being used.

Show how the map_process from tqdm is used to interface with concurrent futures


Usage of shared memory model
----------------------------

why do we care about shared memory model

how to use it in iMars3D


Examples
--------

show some examples


Known issues
------------

Here are several known issues regarding the parallelization in iMars3D:

- Filters that are thin wrapper around ``tomopy`` functions do not have progress bar.
    - An upstream update is needed to bring the support of ``map_process`` to ``tomopy`` natively.
-
