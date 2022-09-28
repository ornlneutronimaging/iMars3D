# package imports
from imars3d.backend.workflow import validate

# standard imports
import json as libjson
from pathlib import Path
from typing import Union


def globals(*args):
    r"""return dictionary of globals"""
    return {arg: None for arg in args}


class Consumer:
    r"""
    tasks :[
    {name: "globals",
     function: "imars3d.backend.workflow.executor.globals"
     args: ["ct", "dc", "ob"]
     outputs: ["globals"]
    }
    {name: "gamma_filter",
     function: "imars3d.backend.corrections.gamma_filter",
     args: ["globals.ct"],
     kwargs:{
       threshold: -1,
       axis: 2
       },
     outputs:["globals.ct"]
    }
    ]
    """
    json = validate.JSONValid(schema=validate.schema)

    def __init__(self, json: Union[str, dict]) -> None:

        # load file or dictionary, with validation against schema
        if isinstance(json, str):
            with open(json, "r") as file_handle:
                json = libjson.load(json)

        self.json = json

    def __call__(self, *args, **kwargs):
        pass
