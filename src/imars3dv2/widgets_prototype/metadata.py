#!/usr/bin/env python3

import param
import panel as pn
from pathlib import Path


class MetaData(param.Parameterized):
    # facility param required to locate the data on
    # analysis mounts
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
    # NOTE: the IPTS-x sub-folder structure is not consistent among
    #       different experiments (historical issues?), so we should
    #       only specify the root, and let users decide where the
    #       input data should be.
    # NOTE: basic dir structure
    #       /FACILITY/INSTRUMENT/IPTS-xxxx/
    #       - raw
    #         |- strucutre unstable, but should always have open-beam, dark current(field), and input ct
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
    #
    # NOTE: recon name will also be used to save intermedia results as well for consistency
    # - intermedia results: temp_root/recon_name/stage_name/data+config
    # - final recon: recn_root/myreon/data+config
    recn_name = param.String(default="myrecon", doc="reconstruction results folder name")

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
        ("data_root", param.Path),
        ("recn_root", param.Path),
        ("temp_root", param.Path),
        ("recn_name", param.String),
    )
    def metadata(self):
        return (
            self.data_root,
            self.recn_root,
            self.temp_root,
            self.recn_name,
        )

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

            > If the information above is correct, proceed to next step.
            """,
            sizing_mode="stretch_width",
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
        cntl_pn = pn.Column(
            inst_input,
            ipts_input,
            projroot_input,
            recnname_input,
            width=width,
        )
        #
        return pn.Row(
            cntl_pn,
            self.summary_pane,
        )
