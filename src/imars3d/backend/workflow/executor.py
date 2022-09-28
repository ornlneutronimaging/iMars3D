def globals(*args):
    "return dictionary of globals"
    return {arg: None for arg in args}


class JsonParser:
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
    pass