#!/usr/bin/env python3
"""Workflow engine for imars3d."""
# package imports
from imars3d.backend.workflow import validate

# standard imports
from collections import namedtuple
from collections.abc import Iterable
import importlib
from typing import Any, List, Optional, Set, Union


class WorkflowEngineError(RuntimeError):
    """Base class for workflow engine errors."""

    pass


class WorkflowEngine:
    @staticmethod
    def _validate_outputs(function_outputs: Union[None, Iterable[Any]]):
        r"""
        Verify the function outputs is either None or a valid iterable.

        Parameters
        ----------
        function_outputs
            Return value of the function carrying out the task

        Raises
        ------
        WorkflowEngineError
        """
        if function_outputs is None:
            return
        tests = {
            "Return value must be an iterable ": hasattr(function_outputs, "__iter__"),
            "Return value cannot be a string": not isinstance(function_outputs, str),
        }
        errors = " and ".join([k for k, v in tests.items() if v is False])
        if errors:
            raise WorkflowEngineError(errors)

    def __init__(self, global_params: Union[Set[str], List[str]]) -> None:
        r"""

        Parameters
        ----------
        global_params
            List of JSON entries deemed as accessible by any workflow task. These are the metadata
            and the task outputs.
        """
        self._global_params: set = set(global_params)
        self._registry: Optional[dict] = None  # will store set or computed globals parameters

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
        module_str, function_name = validate.function_parts(function_str)
        module = importlib.import_module(module_str)
        f = getattr(module, function_name)

        param_names = set(f.param.params().keys())
        outputs = dict(function=f, globals_required=param_names.intersection(self._global_params))
        return namedtuple("TaskFuncionInstrospection", outputs.keys())(**outputs)

    def _update_registry(self, task: dict, function_outputs: Optional[Iterable[Any]] = None) -> None:
        r"""
        Fetch the values for the global parameters that have just been set or computed.

        Parameters
        ----------
        task
            task entry as it appears in the JSON configuration file
        function_outputs
            return value of the function carrying out the task. Should be an iterable, such as a ``List``.

        Raises
        ------
        WorkflowEngineError
            The outputs, as defined in the task entry, don't match the actual return value of the function.
        """
        # insert explicitly passed globals values
        if "inputs" in task:
            globals_explicit = set(task["inputs"]).intersection(self._global_params)
            self._registry.update({k: v for k, v in task["inputs"].items() if k in globals_explicit})
        # insert the outputs of the function carrying out the task
        if "outputs" in task or function_outputs is not None:
            if len(task["outputs"]) != len(function_outputs):
                e = f"Output(s) {task['outputs']} for task {task['name']} don't have corresponding return values"
                raise WorkflowEngineError(e)
            self._registry.update(dict(zip(task["outputs"], function_outputs)))

    def _resolve_inputs(self, inputs: dict, globals_required: set) -> dict:
        r"""Resolve inputs for tasks.

        Populate the input parameters of the parameterized function with whatever global parameters
        it may require and that are missing in the task entry of the JSON configuration file.

        Parameters
        ----------
        inputs
            the "inputs" entry in the JSON configuration file corresponding
            to the task currently being evaluated.
        globals_required
            set of global parameters required as inputs by the parameterized function

        Returns
        -------
        dict
            the inputs for the parameterized function.
        """
        resolved = inputs
        resolved.update({key: None for key in globals_required})  # expand to include implicit globals
        for key in resolved:
            if key in self._registry:
                resolved[key] = self._registry[key]
        return resolved


class WorkflowEngineAuto(WorkflowEngine):
    config = validate.JSONValid()

    @property
    def schema(self):
        r"""Read-only schema file"""
        return self._schema

    def __init__(
        self,
        config: validate.JsonInputTypes,
        schema: Optional[validate.JsonInputTypes] = validate.SCHEMA,
        global_params: Optional[Union[Set[str], List[str]]] = validate.GLOBAL_PARAMS,
    ) -> None:
        r"""Initialize the workflow engine.

        Parameters
        ----------
        config
            JSON configuration for reconstruction-reduction
        schema
        global_params
            List of JSON entries deemed as accessible by any workflow task. These are the metadata
            and the task outputs.
        """
        self._schema: dict = validate._todict(schema)
        self.config: dict = config  # validated JSON configuration file
        super().__init__(global_params)

    def _dryrun(self) -> None:
        r"""Verify validity of the workflow configuration.

        Validate that the inputs of a task, which could be the output(s) of any previous task(s),
        have been computed.

        Raises
        ------
        WorkflowEngineError
            one or more global inputs are not the output(s) of any previous task(s).
        """
        # `current_globals` stores global parameters that have already been computed
        current_globals = set([x for x in self.config if x not in ("name", "tasks")])

        # cycle over each task and carry out the following steps:
        # 1. any global parameter required by task["function"] as input must be accounted for in `current_globals`
        # 2. assume any global parameter in task["inputs"] is being passed an actual value
        #    in `current_globals`
        # 3. update `current_globals` with task["outputs"], if present
        for task in self.config["tasks"]:
            peek = self._instrospect_task_function(task["function"])

            # does the task need globals not explicitly stated as "inputs"?
            globals_explicit = set(task.get("inputs", {})).intersection(self._global_params)
            globals_implicit = peek.globals_required - globals_explicit
            missing = globals_implicit - current_globals
            if missing:
                raise WorkflowEngineError(f"input(s) {', '.join(missing)} for task {task['name']} are missing")

            # mocks running the task
            outputs = None  # noqa F841

            # insert explicitly passed globals values, or computed, after the task is carried out
            if "inputs" in task:
                globals_explicit = set(task["inputs"]).intersection(self._global_params)
                current_globals.update(globals_explicit)
            if "outputs" in task:
                new_globals = set([x for x in task["outputs"] if isinstance(x, str)])
                unaccounted = new_globals - self._global_params  # these parameters should be globals
                if unaccounted:
                    raise WorkflowEngineError(
                        f"Output(s) {', '.join(unaccounted)} of task {task['name']} " "should be global but aren't!"
                    )
                current_globals.update(new_globals)

    def run(self) -> None:
        r"""Sequential execution of the tasks specified in the JSON configuration file."""
        self._dryrun()
        # initialize the registry of global parameters with the metadata
        self._registry = {k: v for k, v in self.config.items() if k not in ("name", "tasks")}
        for task in self.config["tasks"]:
            peek = self._instrospect_task_function(task["function"])
            inputs = self._resolve_inputs(task.get("inputs", {}), peek.globals_required)
            outputs = peek.function(**inputs)
            self._validate_outputs(outputs)
            self._update_registry(task, outputs)
