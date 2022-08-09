#!/usr/bin/env python3

import param
import panel as pn
from panel.widgets import Tqdm
import numpy as np
import tifffile


class ExpMeta(param.Parameterized):
    #
    instrument = param.Selector(default="CG1D", objects=["CG1D", "SNAP", "VENUS", "CUPID"], doc="Imageing instruments")
    #
    facility = param.String(
        default="HFIR",
        doc="facility hosting the instrument",
    )
    #
    scan_name = param.String(
        default="my_scan",
        doc="user defined name for given CT scan",
    )
    #
    output_folder_name = param.String(
        default="my_recon",
        doc="output directory name for reconstruction results",
    )
    #
    IPTS = param.Integer(
        default=0,
        bounds=(0, 100_000_000),
        doc="experiment ID, a.k.a IPTS number",
    )
    #
    proj_root = param.String(
        doc="project root directory",
    )

    @param.depends("IPTS", watch=True)
    def _update_default_scan_name(self):
        if self.scan_name == "my_scan":
            self.scan_name = f"scan_{self.IPTS}"

    @param.depends("IPTS", "scan_name", watch=True)
    def _update_default_output_folder_name(self):
        if self.output_folder_name == "my_recon":
            if self.scan_name == "my_scan":
                self.output_folder_name = f"recon_{self.IPTS}"
            else:
                self.output_folder_name = f"recon_{self.scan_name}"

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

    @param.depends("instrument", "IPTS", watch=True)
    def _update_proj_root(self):
        self.proj_root = f"~/tmp/{self.facility}/{self.instrument}/IPTS-{self.IPTS}"

    def panel(self):
        return pn.Param(
            self.param,
            name="Select instrument and input IPTS number",
            widgets={
                "instrument": pn.widgets.RadioButtonGroup,
                "facility": {
                    "name": "facility",
                    "widget_type": pn.widgets.StaticText,
                },
                "IPTS": {
                    "widget_type": pn.widgets.LiteralInput,
                    "placeholder": "Enter your experiment IPTS number",
                },
                "proj_root": {
                    "name": "project root",
                    "widget_type": pn.widgets.StaticText,
                },
            },
        )


class DataLoader(ExpMeta):
    # container to store images
    ct = param.Array(
        doc="radiograph stack as numpy array",
        precedence=-1,  # hide
    )
    ob = param.Array(
        doc="open beam stack as numpy array",
        precedence=-1,  # hide
    )
    df = param.Array(
        doc="dark field stack as numpy array",
        precedence=-1,  # hide
    )
    # actions/buttons
    load_data_action = param.Action(lambda x: x.param.trigger("load_data_action"), label="Load Data")
    progress_bar = Tqdm(width=500, align="end")

    @param.depends("proj_root")
    def file_selector(self):
        self.radiograph_folder = pn.widgets.FileSelector(
            directory=self.proj_root,
            name="Radiographs(CT)",
        )
        self.openbeam = pn.widgets.FileSelector(
            directory=f"{self.proj_root}",
            name="Open-beam(OB)",
        )
        self.darkfield = pn.widgets.FileSelector(
            directory=f"{self.proj_root}",
            name="Dark-field(DF)",
        )
        return pn.Tabs(self.radiograph_folder, self.openbeam, self.darkfield)

    @param.depends("load_data_action", watch=True)
    def load_data(self):
        self.ct = self.read_tiffs(self.radiograph_folder.value, "CT")
        self.ob = self.read_tiffs(self.openbeam.value, "OB")
        self.df = self.read_tiffs(self.darkfield.value, "DF")

    @param.output(
        ("ct", param.Array),
        ("ob", param.Array),
        ("df", param.Array),
    )
    def get_date(self):
        return self.ct, self.ob, self.df

    def read_tiffs(self, filelist, desc):
        if len(filelist) == 0:
            return None
        data = []
        for me in self.progress_bar(filelist, desc=desc):
            data.append(tifffile.imread(me))
        return np.array(data)

    def panel(self):
        expmeta_pn = ExpMeta.panel(self)
        app = pn.Row(
            expmeta_pn,
            self.file_selector,
            sizing_mode="stretch_width",
        )
        return pn.Column(app, self.progress_bar, sizing_mode="stretch_width")
