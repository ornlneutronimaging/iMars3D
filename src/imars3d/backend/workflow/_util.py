from importlib.util import find_spec
from importlib import import_module
from typing import Tuple


def _function_parts(func_str: str) -> Tuple[str, str]:
    """Convert the function specification into a module and function name."""
    mod_str = ".".join(func_str.split(".")[:-1])
    func_str = func_str.split(".")[-1]

    return (mod_str, func_str)


def function_exists(func_str: str) -> bool:
    """Return True if the function exists."""
    mod_str, func_str = _function_parts(func_str)

    if not bool(find_spec(mod_str, func_str)):
        return False
    module = import_module(mod_str)
    return hasattr(module, func_str)


def get_function_ref(function_str: str):
    """Return reference to the specified function."""
    module_str, function_name = _function_parts(function_str)
    module = import_module(module_str)
    return getattr(module, function_name)
