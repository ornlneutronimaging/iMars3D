imars3d.backend.workflow package
================================

.. automodule:: imars3d.backend.workflow
   :members:
   :undoc-members:
   :show-inheritance:


Submodules
----------

imars3d.backend.workflow.engine module
--------------------------------------

.. automodule:: imars3d.backend.workflow.engine
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: TaskOutputTypes, config, load_data_function, save_data_function

imars3d.backend.workflow.validate module
----------------------------------------

The validation happens in 3 steps:

1. Validate against the `schema <https://github.com/ornlneutronimaging/iMars3D/blob/next/src/imars3d/backend/workflow/schema.json>`_
2. Verify that the facility and instrument are supported
3. Verify that the ``function`` for each steps exists

An individual json configuration can be validated from the command line using `jsonschema <https://python-jsonschema.readthedocs.io/en/stable/>`_

.. code-block:: sh

   jsonschema --instance example.json src/imars3d/backend/workflow/schema.json


The `schema itself <https://github.com/ornlneutronimaging/iMars3D/blob/next/src/imars3d/backend/workflow/schema.json>`_ can be viewed in the code, however it suggests a very flat file.
An `example json configuration from the test suite <https://github.com/ornlneutronimaging/iMars3D/blob/next/tests/data/json/good.json>`_ is linked as another way to understand the format.
The top level of the json configuration file is

+------------+------------+--------------------------------------------------------+----------+
|            | Type       | Description                                            | Required |
+============+============+========================================================+==========+
| facility   | ``string`` | Facility for the measurment                            | Y        |
+------------+------------+--------------------------------------------------------+----------+
| instrument | ``string`` | Instrument for the measurment                          | Y        |
+------------+------------+--------------------------------------------------------+----------+
| ipts       | ``string`` | The full IPTS identifier for the measurement           | Y        |
+------------+------------+--------------------------------------------------------+----------+
| name       | ``string`` | Rememberable name for the measurement                  | Y        |
+------------+------------+--------------------------------------------------------+----------+
| workingdir | ``string`` | Directory to write intermediate results when requested | Y        |
+------------+------------+--------------------------------------------------------+----------+
| outputdir  | ``string`` | Directory to write final results                       | Y        |
+------------+------------+--------------------------------------------------------+----------+
| tasks      | ``array``  | Each task is a step in the tomographic reconstruction  | Y        |
+------------+------------+--------------------------------------------------------+----------+

Tasks contain the following elements

+------------+------------+--------------------------------------------------------+----------+
|            | Type       | Description                                            | Required |
+============+============+========================================================+==========+
| name       | ``string`` | Friendly name for the task                             | Y        |
+------------+------------+--------------------------------------------------------+----------+
| function   | ``string`` | Fully qualified python name for the task               | Y        |
+------------+------------+--------------------------------------------------------+----------+
| inputs     | ``object`` | Dictionary of inputs to the task. These are in the     | N        |
|            |            | form of key value pairs that are passed into the task. |          |
+------------+------------+--------------------------------------------------------+----------+
| outputs    | ``array``  | List of outputs from the task                          | N        |
+------------+------------+--------------------------------------------------------+----------+

Since not all tasks require inputs and outputs, they are optional.

.. automodule:: imars3d.backend.workflow.validate
   :members:
   :undoc-members:
   :show-inheritance:
