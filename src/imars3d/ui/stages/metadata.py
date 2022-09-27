#!/usr/bin/env python3
"""
First stage to generate interactive reconstruction
"""
import param
import panel as pn
from pathlib import Path
from imars3d.backend.io.config import save_config


class MetaData(param.Parameterized):
    # configuration to carry into the next stage
    config_dict = param.Dict(
        default={
            "facility": "TBD",
            "instrument": "TBD",
            "ipts": 0,
            "projectdir": "TBD",
            "name": "TBD",
            "workingdir": "TBD",
            "outputdir": "TBD",
            "steps": [],
        } ,
        doc="Configuration dictionary",
    )
    # basic input
    instrument = param.Selector(
        default="CG1D",
        objects=["CG1D", "SNAP", "VENUS", "CUPID"],
        doc="name of neutron imaging instrument",
    )
    facility = param.String(default="HFIR", doc="hosting facility of instrument")
    ipts_num = param.Integer(
        default=0,
        bounds=(0, None),
        doc="IPTS number",
    )
    # derived project root
    # NOTE: the IPTS-x sub-folder structure is not consistent among different experiments,
    #       so we should only specify the root, and let users decide where the input data should be.
    # NOTE: basic dir structure
    #       /FACILITY/INSTRUMENT/IPTS-xxxx/
    #       - raw
    #         |- strucutre unstable, but should always have open-beam, dark current, and input ct
    #       - shared
    #         |- processed_data
    #            |- where reconstruction results sits in each own folder
    #       - etc. (does not related to reconstruction process)
    proj_root = param.Path(
        default=Path.home(),
        search_paths=[Path.home() / Path("tmp"), Path("/")],  # add ~/tmp for local development purpose
        doc="experiment root directory",
    )
    data_root = param.Path(
        default=Path.home(),
        doc="ct, ob, and df root directory, default should be proj_root/raw",
    )
    recn_root = param.Path(
        default=Path.home(),
        doc="reconstruction results root, default should be proj_root/processed_data",
    )
    temp_root = param.Path(
        default=Path.home() / Path("tmp"),
        doc="intermedia results save location",
    )
    recn_name = param.String(default="myrecon", doc="reconstruction results folder name")
    save_config_to_disk = param.Action(lambda x: x.param.trigger("save_config_to_disk"))
    
    @param.depends("save_config_to_disk", watch=True)
    def save_config_file(self):
        config_filename = str(Path(self.recn_root) / self.recn_name / f"{self.recn_name}.json")
        save_config(self.config_dict, config_filename)

    @param.depends("instrument", watch=True)
    def _update_facility(self):
        if self.instrument in ("CG1D"):
            self.facility = "HFIR"
        elif self.instrument in ("SNAP", "VENUS"):
            self.facility = "SNS"
        elif self.instrument in ("CUPID"):
            self.facility = "STS"
        else:
            self.facility = "???"

    @param.depends("instrument", "ipts_num", "facility", watch=True)
    def _update_proj_root(self):
        self.proj_root = f"{self.facility}/{self.instrument}/IPTS-{self.ipts_num}"

    @param.depends("proj_root", watch=True)
    def _update_roots(self):
        self.data_root = f"{self.proj_root}/raw"
        self.recn_root = f"{self.proj_root}/shared/processed_data"

    @param.output(
        ("config_dict", param.Dict),
    )
    def as_dict(self):
        return self.config_dict

    def summary_pane(self):
        return pn.pane.Markdown(
            f"""
            # Summary for reconstruction: {self.recn_name}
            ----------------------------------------------

            | Derived Category | Info |
            | -------- | ------ |
            | Instrument | {self.instrument}@{self.facility} |
            | Experiment root dir | `{self.proj_root}`|
            | Raw data dir | `{self.data_root}` |
            | Results dir | `{Path(self.recn_root) / Path(self.recn_name)}` |
            | Checkpoint(s) dir | `{Path(self.temp_root) / Path(self.recn_name)}` |
            | Configuration | `{Path(self.temp_root) / Path(self.recn_name) / f"{Path(self.recn_name)}.json"}` |

            > If the information above is correct, proceed to next step.
            """,
            sizing_mode="stretch_width",
        )
    
    @param.depends(
        "instrument",
        "ipts_num",
        "facility",
        watch=True,
    )
    def _update_config(self):
        self.config_dict["instrument"] = self.instrument
        self.config_dict["ipts"] = self.ipts_num
        self.config_dict["facility"] = self.facility
        self.config_dict["projectdir"] = self.proj_root
        self.config_dict["name"] = self.recn_name
        self.config_dict["workingdir"] = self.temp_root
        self.config_dict["outputdir"] = self.recn_root

    @param.depends(
        "instrument",
        "ipts_num",
        "facility",
        "config_dict",
    )
    def panel(self, width=250):
        inst_input = pn.widgets.Select.from_param(
            self.param.instrument,
            name="Instrument",
            tooltips="Select instrument",
        )
        ipts_input = pn.widgets.LiteralInput.from_param(
            self.param.ipts_num,
            name="IPTS",
            tooltips="Enter IPTS number",
        )
        projroot_input = pn.widgets.TextInput.from_param(
            self.param.proj_root,
            name="Project root",
            placeholder="Enter non-standard project root manually here...",
        )
        recnname_input = pn.widgets.TextInput.from_param(
            self.param.recn_name, name="Reconstrution name", placeholder="Enter a name for your reconstruction..."
        )
        save_json_button = pn.widgets.Button.from_param(self.param.save_config_to_disk, name="Save Config")
        cntl_pn = pn.Column(
            inst_input,
            ipts_input,
            projroot_input,
            recnname_input,
            save_json_button,
            width=width,
        )
        #
        interactive_app = pn.Row(
            cntl_pn,
            self.summary_pane,
        )
        json_editor = pn.widgets.JSONEditor.from_param(
            self.param.config_dict,
            mode="view",
            menu=False,
            sizing_mode="stretch_width",
        )
        config_viewer = pn.Card(
            json_editor,
            title="CONFIG Viewer",
            sizing_mode="stretch_width",
            collapsed=True,
        )
        #
        app = pn.Column(
            interactive_app,
            config_viewer,
            sizing_mode="stretch_width",
        )
        return app
