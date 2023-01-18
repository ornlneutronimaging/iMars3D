==============================
How to Write Integration Tests
==============================

The Data Repository
===================

Integration tests will typically require data from the **data repository**
located in ``iMars3D/tests/data/imars3d-data/`` as a
`git submodule <https://git-scm.com/book/en/v2/Git-Tools-Submodules>`_.

TL;DR
-----

Perform the following steps after cloning the repo and ``cd`` to the root of the repo:

- ``sudo apt install git-lfs``  (if not already installed)
- ``git submodule init``
- ``git submodule update``

Now you should have the integration test data downloaded to ``iMars3D/tests/data/imars3d-data/``.
If you are interested in how it is configured, please continue reading.

Git Submodule
-------------

**tutorials:**

- `atlassian <https://www.atlassian.com/git/tutorials/git-submodule>`_
- `sitepoint <https://www.sitepoint.com/git-submodules-introduction/>`_

**typical commands:**

Here, "submodule" refers to repo ``imars3d-data`` and "parent" refers to repo ``imars3d``

- checkout the submodule after cloning the parent with command ``git submodule init``
- find the refspec stored in the parent with command ``git ls-tree $(git branch --show-current) tests/data/imars3d-data``
- synchronize the submodule to the refspec stored in the parent with command ``git submodule update``
- after making commits in the sumodule, synchronize the refspec stored in the parent with commands ``git add...` and `git commit...``

Pytest Fixtures
===============

Pytest fixtures in ``conftest.py`` providing directories frequently accessed:

+--------------+----------------------------------------------------------------------------+
| Fixture      | Value (as a `pathlib.Path` object)                                         |
+==============+============================================================================+
| DATA_DIR     | iMars3D/tests/data/imars3d-data                                            |
+--------------+----------------------------------------------------------------------------+
| IRON_MAN_DIR | iMars3D/tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man |
+--------------+----------------------------------------------------------------------------+

Writing Test Functions
======================

Test functions accessing ``DATA_DIR`` should be marked with the ``datarepo`` marker

.. code:: python

   @pytest.mark.datarepo
   def test_function(DATA_DIR):
       pass
