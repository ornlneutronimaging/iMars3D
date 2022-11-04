#!/usr/bin/env python3
"""Workflow engine for imars3d."""
# package imports
from ._util import get_function_ref
from imars3d.backend.workflow import validate

# third-party imports
import param as libparam

# standard imports
from collections import namedtuple
from collections.abc import Iterable
import importlib
import json
import numpy as np
from typing import Any, List, Optional, Set, Union


class WorkflowEngineError(RuntimeError):
    """Base class for workflow engine errors."""

    pass


class WorkflowEngine:
    TaskOutputTypes = (None, list, tuple)

    @staticmethod
    def _validate_outputs(task_outputs: TaskOutputTypes, function_outputs: Optional[Any] = None) -> (tuple, None):
        r"""
        Verify the function outputs is a valid iterable and of same length as task["outputs"].

        Parameters
        ----------
        function_outputs
            Return value of the function carrying out the task

        Raises
        ------
        WorkflowEngineError
        """

        def validate_type(outputs):
            if not isinstance(outputs, (list, tuple)):
                raise WorkflowEngineError("Task outputs must be a list or a tuple")

        validate_type(task_outputs)
        if function_outputs is not None:
            if not isinstance(function_outputs, (list, tuple)):
                function_outputs = (function_outputs,)
            # import pdb; pdb.set_trace()
            if len(task_outputs) != len(function_outputs):
                error = "Task and Function have different number of outputs"
                raise WorkflowEngineError(error)
        return function_outputs

    def __init__(self) -> None:
        self._registry: Optional[dict] = None  # will store set or computed parameters

    def _instrospect_task_function(self, function_str: str) -> namedtuple:
        r"""Obtain information from the function associated to one task in the workflow.

        Parameters
        ----------
        function_str
            Literal name for the ``ParameterizedFunction` derived class

        Returns
        -------
        namedtuple
            Fields of the namedtuple ``TaskFuncionInstrospection``:
            function : ParameterizedFunction
                a reference to the function object
            globals_required : set[str]
                the function arguments that are globals, i.e., the names of param.Parameter objects
                that are the outputs of other functions or are part of the metadata.
        """
        # load the ParameterizedFunction derived class associated to the function string
        module_str = ".".join(function_str.split(".")[:-1])
        module = importlib.import_module(module_str)
        function_name = function_str.split(".")[-1]
        f = getattr(module, function_name)
        # Some functions, like `load_data`, have parameters that may or may not be needed
        # depending on the value of other parameters. Methods `dryrun()` assume that
        # parameters are independent of each other
        independent = False if function_name in ["load_data"] else True
        outputs = dict(function=f, paramdict=f.params(), params_independent=independent)
        return namedtuple("TaskFuncionInstrospection", outputs.keys())(**outputs)

    def _resolve_inputs(self, task_inputs: dict, paramdict: dict) -> dict:
        r"""Populate the required parameters missing from the task's `inputs` entry with the contents of the registry

        Parameters
        ----------
        task_inputs
            the "inputs" entry in the JSON configuration file for the task being evaluated.
        paramdict
            dictionary of `name: instance` parameters for the task being evaluated

        Returns
        -------
        dict
            all necessary inputs for the function to be evaluated
        """
        inputs = dict()
        for pname, parm in paramdict.items():
            if pname == "name":  # not an actual input parameter, just an attribute of the function
                continue
            if pname in task_inputs:  # value passed explicitly, but it could refer to a value stored in the registry
                val = task_inputs[pname]
                if isinstance(val, str):  # Examples: `"array": "ct"`, `"exec_mode": "f"`
                    if isinstance(parm, (libparam.Foldername, libparam.String)):
                        if val in self._registry:  # val is a reference to a value stored in the registry
                            inputs[pname] = self._registry[val]  # Example: "savedir": "outputdir"
                        else:  # val is an explicit value
                            inputs[pname] = val  # Example: "ct_dir": "/home/path/to/ctdir/"
                    else:  # must be a reference to a value stored in the registry
                        inputs[pname] = self._registry[val]  # Example: "array": "ct"
                else:
                    inputs[pname] = val  # Example: "rot_center": 0.0
            elif pname in self._registry:  # implicit
                inputs[pname] = self._registry[pname]
        return inputs


class WorkflowEngineAuto(WorkflowEngine):
    config = validate.JSONValid()

    def __init__(self, config: validate.JsonInputTypes) -> None:
        r"""Initialize the workflow engine.

        Parameters
        ----------
        config
            JSON configuration for reconstruction-reduction
        """
        self.config: dict = config  # validated JSON configuration file
        super().__init__()

    def _dryrun(self) -> None:
        r"""Verify validity of the workflow configuration.

        Validate that the inputs of a task, which could be the output(s) of any previous task(s),
        have been computed.

        Raises
        ------
        WorkflowEngineError
            one or more global inputs are not the output(s) of any previous task(s).
        """
        # registry stores parameters that have already been set or computed. Initialize with metadata
        registry = set([x for x in self.config if x not in ("name", "tasks")])

        for task in self.config["tasks"]:
            peek = self._instrospect_task_function(task["function"])
            if peek.params_independent:
                # are all explicitly passed input parameters actual input parameters of this function?
                unacounted = set(task.get("inputs", set())) - set(peek.paramdict)
                if unacounted:
                    pnames = ", ".join([f'"{p}"' for p in unacounted])
                    raise WorkflowEngineError(f"Parameter(s) {pnames} are not input parameters of {task['function']}")
                # assess each function parameter. Is it missing?
                missing = set([])
                for pname, parm in peek.paramdict.items():
                    if pname == "name":  # not an actual input parameter, just an attribute of the function
                        continue
                    if pname == "tqdm_class":
                        continue  # parameter for connecting progress bars to the gui
                    if parm.default is not None:  # the parameter has a default value
                        continue  # irrelevant if parameter value is missing
                    if pname in task.get("inputs", {}):  # parameter explicitly set
                        val = task["inputs"][pname]  # is "val" an actual value or a registry key?
                        if isinstance(val, str):  # Examples: `"array": "ct"`, `"exec_mode": "f"`
                            if isinstance(parm, libparam.String):
                                continue  # In "exec_mode": "f", is "f" a registry key or an actual exec_mode value?
                            if val not in registry:  # "val" is a templated value, so it should be a registry key
                                missing.add(val)

                            continue
                        else:  # parameter is explicitly set. Example: "rot_center": 0.2
                            continue
                    # From here on, the parameter has no default value and has not been set in task["inputs"]
                    if pname not in registry:
                        missing.add(pname)
                if missing:
                    pnames = ", ".join([f'"{p}"' for p in missing])
                    raise WorkflowEngineError(f"Input(s) {pnames} for task {task['name']} are missing")
            # update the registry with contents of task["outputs"]
            if task.get("outputs", []):
                self._validate_outputs(task["outputs"])
                registry.update(set(task["outputs"]))

    def run(self) -> None:
        r"""Sequential execution of the tasks specified in the JSON configuration file."""
        self._dryrun()
        # initialize the registry of global parameters with the metadata
        self._registry = {k: v for k, v in self.config.items() if k not in ("name", "tasks")}
        for task in self.config["tasks"]:
            peek = self._instrospect_task_function(task["function"])
            inputs = self._resolve_inputs(task.get("inputs", {}), peek.paramdict)
            outputs = peek.function(**inputs)
            if task.get("outputs", []):
                outputs = self._validate_outputs(task["outputs"], outputs)
                self._registry.update(dict(zip(task["outputs"], outputs)))
