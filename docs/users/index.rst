===========
User Guide
===========

There are 3 basic entry-points for imars3d

Command line interface
----------------------

The backend can be invoked using the information in :mod:`imars3d.backend <imars3d.backend.__main__>`

Autoreduction
-------------

Autoreduction is triggered by the `data workflow system <https://data-workflow.readthedocs.io/>`_ that powers https://monitor.sns.gov.
A simplified version of what happens, is that the system will run the python script using `mantidpython wrapper <https://github.com/neutrons/post_processing_agent/blob/main/scripts/mantidpython.py>`_ to select a conda environment to activate (denoted in the script using ``CONDA_NAME`` then run

.. code-block:: sh

   /HFIR/CG1D/shared/autoreduce/reduce_CG1D.py /path/to/file /HFIR/CG1D/proposal/shared/autoreduce

The script will decide if the CT measurement is complete, and run autoreconstruction if appropriate.
``reduce_CG1D.py`` is stored in this repository, but needs to be copied into place by hand.

Jupyter notebook
----------------

Start a Jupyter notebook with the kernel that has ``imars3d`` properly installed.
In the first cell, execute the following command to load the necessary extension.

.. code-block:: python

   import panel as pn
   import holoview as hv
   from imars3d.ui.main import MainWindow

   pn.extension(
      "vtk",  # for the 3D viewer
      "terminal",  # or the console
      "jsoneditor",  # for config viewer
      nthreads=0,  # default to use infinite
      notifications=True,  # allow panel notification banner to pop-up
   )
   hv.extension("bokeh")  # use default plotting backend bokeh

Wait for the kernel to return to idle (the extension loading time varies depending on the system).
Then execute the following command to create the main window

.. code-block:: python

   main_window = MainWindow()

There are four ways to render the main window:

- Direct render with ``main_window``.
- Wrap app in a ``panel`` layout, i.e. ``pn.panel(main_window)``.
- Set the app to be servable, i.e. ``main_window.servable()``.
- Start a bokeh server and render the app in a separate tab, i.e. ``main_window.show()``.

For the last method, make sure you are allowed to use additional ports on the system to avoid access error.
