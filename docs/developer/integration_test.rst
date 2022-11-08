==============================
How to Write Integration Tests
==============================

The Data Repository
===================

Integration tests will typically require data from the **data repository**
located in `iMars3D/tests/data/imars3d-data/` as a
git submodule.



Pytest Fixtures
===============

Pytest fixtures in `conftest.py` providing directories frequently accessed:

+--------------+----------------------------------------------------------------------------+
| Fixture      | Value (as a `pathlib.Path` object)                                         |
+==============+============================================================================+
| DATA_DIR     | iMars3D/tests/data/imars3d-data                                            |
+--------------+----------------------------------------------------------------------------+
| IRON_MAN_DIR | iMars3D/tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man |
+--------------+----------------------------------------------------------------------------+

Writing Test Functions
======================

Test functions accessing `DATA_DIR` should be marked with the `datarepo` marker

.. code:: python

   @pytest.mark.datarepo
   def test_function(DATA_DIR):
       pass
