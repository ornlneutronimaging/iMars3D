=======================
Development Environment
=======================

.. contents::
    :local:


Setup Local Development Environment
-----------------------------------

To setup a local development environment, the developers should follow the steps below:

* Install ``anaconda`` (``miniconda`` is recommended)
* Clone the repository and make a feature branch based off ``next``.
* Create a new virtual environment with ``conda env create`` which uses ``environment.yml``

.. code-block:: sh

   conda env create --file environment.yml

* Activate the virtual environment with ``conda activate imars3d``
* Activate the pre-commit hooks

.. code-block:: sh

   pre-commit install

* Configure `playwright <https://playwright.dev/python/docs/intro>`_ for running gui tests ``playwright install``

The ``environment.yml`` contains all of the dependencies for both the developer and the build servers.
Update file ``environment.yml`` if dependencies are added to the package.


Test Data
---------

The test data (currently 5GB) is stored in a second git repository `imars3d-data <https://code.ornl.gov/sns-hfir-scse/infrastructure/test-data/imars3d-data>`_ which uses git-lfs.
To use it, first install git-lfs, then setup the git-submodule

.. code-block:: sh

   git submodule init
   git submodule update

Useful Functions
----------------

The [cache](https://docs.python.org/3/library/functools.html#functools.cache) decorator can be used to hold onto returns of functions.
The data is stored in a ``dict`` with the function parameters as the key, and the return as the value.
The cache remains in memory for the lifetime of the pytest run and a [pytest fixture](https://docs.pytest.org/en/7.1.x/how-to/fixtures.html) with more limited scope may be more appropriate.

Access Development Version on Analysis Cluster
----------------------------------------------

If the local machine does not have enough resources (disk space or memory) for the development environment, the developers can access the development version on the analysis cluster.
In order to run the testing notebook on the analysis cluster, the developers need to install the development environment as a local Jupyter kernel following the steps below:

* Make sure ``conda`` can find the ``imars3d`` environment.
* From the command line, run ``python -m ipykernel install --user --name imars3d --display-name "imars3d_localdev"``.
* Double check that the kernel is installed at ``~/.local/share/jupyter/kernels/imars3d``.
* Start the notebook server from the command line with ``jupyter notebook`` and select the new kernel for testing with notebooks.
