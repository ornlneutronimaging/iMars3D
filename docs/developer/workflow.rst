===============
Workflow Engine
===============

.. contents::
    :local:

The *workflow engine*  digests the JSON file by generating a sequence of function calls.
The input values to any one function may depend on the output(s) of previous function(s).
The *workflow state manager* (WSM) will store at any point in the workflow execution
the necessary data to call the next function.
Outputs of previous functions are stored in the WSM.

Use-case: Loading Data
----------------------

Roles:

* ``User``
* ``UI``
* Workflow Engine (a.k.a ``Engine``)
* ``Backend``

.. image:: media/load_data.png
    :width: 800px
    :align: center
    :alt: sequence diagram when loading data
