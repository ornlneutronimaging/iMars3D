===========
User Guide
===========

There are 3 basic entrypoints for imars3d

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

TBD
