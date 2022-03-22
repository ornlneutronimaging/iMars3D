=======
Release
=======

.. contents::
    :local:


Overview
--------

The release of iMars3D is configured to be done by an automated pipeline via Github action.
However, developers might have to create manual releases in case the automated system fails, the process of which requires a working local development.
For iMars3D, there are three official release channels, and this document will provide necessary information on how to release iMars3D to all three.


Release to PyPI
---------------

Only the stable version of iMars3D should be published to PyPI.
To publish a new stable version, the following steps are required:

* Checkout the ``main`` branch and make sure it is updated.
* Increase the version number in ``setup.cfg`` if it has not been increased.
* In the root directory of the repository, run ``python -m build`` to build the wheel.

  * The wheel file will be created in the ``dist`` directory.
  * The name of the wheel should following the standard convention, i.e. ``imars3d-<version>-py3-none-any.whl``.

* Upgrade your local PyPI publishing tool with ``python -m pip install --upgrade twine``.
* Upload the wheel file to PyPI with ``python -m twine upload --repository imars3d dist/*.whl``.

For more information on how to publish to PyPI, please refer to the official documentation: https://packaging.python.org/en/latest/tutorials/packaging-projects/


Release to Conda
----------------

The stable version of iMars3D should be released to ``conda-forge`` channel, and the nightly version should be released to the project channel, ``neutronimaging``.

To build the nightly version, the following steps are required:

* Make sure the local development environment has both ``anaconda-client`` and ``conda-build`` installed.
* Checkout the branch ``next``.
* Build the package with ``conda build .``.
* Use ``conda build . --output`` to locate the built package.
* Upload package to ``neutronimaging`` account

  * Contact senior developers for the account credential of ``neutronimaging``.
  * Login from command line with ``anaconda login``.
  * Upload with ``anaconda upload $PACKAGE_PATH`` where ``$PACKAGE_PATH`` is the path to the built package.

To build the stable version for ``conda-forge``, the following steps are required:

* Junior developers: STOP!! Contact the maintainer (one of the senior developers) to build and deploy the stable version manually.
* Maintainer: Follow the official conda-forge `instructions`_ on adding package.

.. _instructions: https://conda-forge.org/docs/maintainer/adding_pkgs.html
