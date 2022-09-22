=======================
Development Environment
=======================

.. contents::
    :local:


Setup Local Development Environment
-----------------------------------

To setup a local development environment, the developers should follow the steps below:

* Install ``anaconda`` via either standard ``anaconda`` or ``miniconda``.
* Clone the repository and make a feature branch based off ``next``.
* Create a new virtual environment with ``conda env create -f conda_development.yml``.
* Activate the virtual environment with ``conda activate imars3d``.

Update file ``conda_environment.yml`` if dependencies are added to the package,
except if those dependencies are needed only for testing. In this case, update
file ``conda_development.yml``.


Access Development Version on Analysis Cluster
----------------------------------------------

If the local machine does not have enough resources (disk space or memory) for the development environment, the developers can access the development version on the analysis cluster.
In order to run the testing notebook on the analysis cluster, the developers need to install the development environment as a local Jupyter kernel following the steps below:

* Make sure ``conda`` can find the ``imars3d`` environment.
* From the command line, run ``python -m ipykernel install --user --name imars3d --display-name "imars3d_localdev"``.
* Double check that the kernel is installed at ``~/.local/share/jupyter/kernels/imars3d``.
* Start the notebook server from the command line with ``jupyter notebook`` and select the new kernel for testing with notebooks.
