# package imports
from imars3d.backend.workflow import validate

# third party imports
from param import ParameterizedFunction

# standard imports
from collections import namedtuple
import importlib
from typing import List, Union


class WorkflowEngineError(RuntimeError):
    pass


def WorkflowEngine(config: Union[str, dict], schema: str = validate.SCHEMA) -> "WorkflowEngineWithSchema":  # noqa F821
    r"""engine thant interprets and runs all the operations in the reconstruction configuration

    Parameters
    ----------
    config
        JSON configuration for reconstruction-reduction
    schema
        JSON schema for validation of `config`

    Returns
    -------
        Instance of class WorkflowEngineWithSchema
    """
    class WorkflowEngineWithSchema:
        config = validate.JSONValid(schema=schema)
        # parameters that can potentially be shared by more than one task
        # REVIEW could be added in the schema instead of hardcode it here
        global_params = {"instrument",
                         "ipts",
                         "workingdir",
                         "outputdir",
                         "ct",  # array of radiograph intensities
                         "ob",  # array of open bean intensities
                         "dc",  # array of dark current intensities
                         "tilt_angle",
                         "rot_center"
                         }

        @staticmethod
        def _init_registry() -> dict:
            return {k: v for k, v in config.items() if k != "tasks"}

        @staticmethod
        def _load_function(function_str: str) -> ParameterizedFunction:
            r"""

            Parameters
            ----------
            function_str

            """
            module_str = ".".join(function_str.split(".")[:-1])
            module = importlib.import_module(module_str)
            function_name = function_str.split(".")[-1]
            return getattr(module, function_name)

        @staticmethod
        def _instrospect_task_function(function_str: str, ) -> namedtuple:
            r"""Obtain information from a task function

            Parameters
            ----------
            function_str

            Returns
            -------
            namedtuple
                Fields of the namedtuple ``TaskFuncionInstrospection``:
                function : ParameterizedFunction
                    a reference to the function object
                param_names : set[str]
                    the names of the function arguments, which are the names of param.Parameter objects
            """
            f = WorkflowEngineWithSchema._load_function(function_str)
            outputs = dict(function=f,
                           param_names=set(f.param.params().keys()))
            return namedtuple('TaskFuncionInstrospection', outputs.keys())(**outputs)

        def __init__(self) -> None:
            r"""

            Parameters
            ----------
            config
                JSON configuration for reconstruction-reduction
            """
            self.config = config
            self._registry = None

        def _update_registry(self, registry_keys: List, values: List) -> None:
            r"""

            Parameters
            ----------
            registry_keys
            values

            Returns
            -------

            """
            assert len(registry_keys) == len(values)
            for k, v in zip(registry_keys, values):
                self._registry[k] = v  # overwrite or create new registry entry

        def _resolve_inputs(self, inputs: dict) -> dict:
            r"""Some values in dict `inputs` may be keys of the registry.
             Substitute with values of the registry if true.
            """
            resolved = inputs
            for key, possible_reg_key in inputs.items():
                if possible_reg_key in self._registry:
                    resolved[key] = self._registry[possible_reg_key]
            return resolved

        def _dryrun(self) -> None:
            r"""Validate that the inputs of a task which could be the output of a previous task have been computed

            Raises
            ------
            RuntimeError
                one or more inputs are not the output(s) of the previous tasks
            """
            # `current_globals` stores global parameters that have already been computed
            current_globals = set([x for x in self.config if x not in ("name", "tasks")])

            # cycle over each task and carry out the following steps:
            # 1. any global parameter required by task["function"] as input must be accounted for in `current_globals`
            # 2. any templated parameter in task["inputs"] referring to a global parameter must be accounted for
            #    in `current_globals`
            # 3. update `current_globals` with task["outputs"], if present
            for task in self.config["tasks"]:
                peek = self._instrospect_task_function(task["function"])

                globals_required = peek.param_names.intersection(self.global_params)
                templated = set([x for x in task.get("inputs", {}).values() if isinstance(x, str)])
                globals_required.update(templated.intersection(self.global_params))
                missing = globals_required - current_globals
                if missing:
                    raise WorkflowEngineError(f"input(s) {', '.join(missing)} for task {task['name']} are missing")

                # insert recently computed globals, after the task is carried out
                if "outputs" in task:
                    new_globals = set([x for x in task["outputs"] if isinstance(x, str)])
                    unaccounted = new_globals - self.global_params  # these parameters should be globals
                    if unaccounted:
                        raise WorkflowEngineError(f"Output(s) {', '.join(unaccounted)} of task {task['name']} "
                                                  "should be global but aren't!")
                    current_globals.update(new_globals)

        def run(self) -> None:
            r"""Execute the tasks specified in the configuration file"""
            self._dryrun()
            self._registry = WorkflowEngineWithSchema._init_registry()
            for task in self.config["tasks"]:
                function = WorkflowEngineWithSchema._load_function(task["function"])
                inputs = self._resolve_inputs(task["inputs"])
                outputs = function(**inputs)
                if outputs:
                    self._update_registry(task["outputs"], outputs)

    return WorkflowEngineWithSchema()
