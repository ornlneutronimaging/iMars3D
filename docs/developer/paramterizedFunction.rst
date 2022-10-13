Parameterized function
======================

Background
----------

All user-facing functions in this library should have built-in inputs validation.
This is done by using the `param`_ library where

- the inputs type can be validated without using 3rd-party interpreter like ``pypy``.
- bounds check are performed prior to the function execution.
- corresponding front end can use the built-in type check to semi-automatically generate the ui code based off its sibling library, `panel`_.


Usage example
-------------

Let's assume that we need to convert the following generic Python function into a parameterized function:

.. code-block:: python

    def add(base: float, phase:float, exponent: int) -> float:
        return (base + phase) ** exponent

The very first step would be making the original function a ``private`` function by adding a leading underscore,
which will prevent ``sphinx`` to generate the documentation for it.

.. code-block:: python

    def _add(base: float, phase:float, exponent: int) -> float:
        return (base + phase) ** exponent

Then, we can use the ``param.ParameterizedFunction`` to create a callable function as the user-facing wrapper:

.. code-block:: python

    import param

    class add(param.ParameterizedFunction):
        """
        Callable functions demo

        Parameters
        ----------
        base : float
            The base value
        phase : float
            The phase value
        exponent : int
            The exponent value

        Returns
        -------
        float
            The result of the calculation
        """
        base = param.Number(default=0, bounds=(0, 1), doc="base value")
        phase = param.Number(default=0, bounds=(0, 1), doc="phase value")
        exponent = param.Integer(default=0, bounds=(0, 10), doc="exponent value")

        def __call__(self, **params) -> float:
            # forced type+bounds check
            _ = self.instance(**params)
            # sanitize
            # NOTE: this will allow param to use default value if the input arg
            #       is missing from params.
            #       for example, if we call add(base=1, exponent=2), then param
            #       here will help fill in the missing arg, phase with its default
            #       i.e.  _add(base=1, phase=0, exponent=2)
            params = param.ParamOverrides(self, params)
            # call the actual function
            base = params.get("base")  # alternatively, params.base
            phase = params.get("phase")  # alternatively, params.phase
            exponent = params.get("exponent")  # alternatively, params.exponent
            return _add(base, phase, exponent)

Notice that the function docstring is added to the class docstring location with explicit type attention.
This is because we want ``sphinx`` to render this as close as possible to the original function.
The ``__call__`` method is the only method that is required to be implemented, and it is possible to achieve polymorphism here if needed.


Unit tests
----------

The original unit test function should be able cover the wrapper.

.. code-block:: python

    import pytest

    def test_add():
        assert add(base=1.0, phase=0.2, exponent=2) == 1.44

However, if the logic inside ``__call__`` is complicated, it is better to use ``unittest.mock`` to isolate logics and test the private functions independently.
For more information, please refer to the `unittest.mock`_ documentation.


Generate widget from parameterized function
-------------------------------------------

For simple function ``add``, we can use the auto translation from panel to create a widget:

.. code-block:: python

    import panel as pn

    pn.extension()
    # auto translate input to widget
    pn.Param(add.param)

However, complicated layout would still require the developer to extract the underlying parameters from the wrapped function, and manually create widget via

.. code-block:: python

    pn.widget.FloatSlider.from_param(add.param.base)

Tha main benefit here is that we can keep the type and bounds check in the backend and only use the widget to collect the user input.


Further reading
---------------

Please refer to the official `param`_ and `panel`_ documentation for more information.


.. _param: https://param.holoviz.org/
.. _panel: https://panel.holoviz.org/
.. _unittest.mock: https://docs.python.org/3/library/unittest.mock.html
