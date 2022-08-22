#!/usr/bin/env python3

import os
import numpy as np
import tifffile
from pathlib import Path
import param
import panel as pn
from panel.widgets import Tqdm


class DataLoader(param.Parameterized):
    # input from previous step
    data_root = param.Path(
        default=Path.home(),
        doc="ct, ob, and df root directory, default should be proj_root/raw",
    )
    proj_root = param.String(doc="map data_root to string to avoid a FileSelector error")
    recn_root = param.Path(
        default=Path.home(),
        doc="reconstruction results root, default should be proj_root/processed_data",
    )
    temp_root = param.Path(
        default=Path.home() / Path("tmp"),
        doc="intermedia results save location",
    )
    recn_name = param.String(
        default="myrecon",
        doc="reconstruction results folder name",
    )
    # data container
    ct = param.Array(
        doc="radiograph stack as numpy array",
        precedence=-1,  # hide
    )
    ob = param.Array(
        doc="open beam stack as numpy array",
        precedence=-1,  # hide
    )
    dc = param.Array(
        doc="dark current stack as numpy array",
        precedence=-1,  # hide
    )
    omegas = param.Array(
        doc="rotation angles in degress derived from tiff filename.",
    )
    # load data action
    load_data_action = param.Action(lambda x: x.param.trigger("load_data_action"))
    progress_bar = Tqdm(width=300, align="end")

    @param.depends("data_root")
    def _update_proj_root(self):
        self.proj_root = str(self.data_root)

    @param.depends("proj_root")
    def file_selector(self):
        self.radiograph_folder = pn.widgets.FileSelector(
            directory=self.data_root,
            name="Radiographs(CT)",
        )
        self.openbeam = pn.widgets.FileSelector(
            directory=self.data_root,
            name="Open-beam(OB)",
        )
        self.darkcurrent = pn.widgets.FileSelector(
            directory=self.data_root,
            name="Dark-current(DC)",
        )
        return pn.Tabs(self.radiograph_folder, self.openbeam, self.darkcurrent)

    @param.depends("load_data_action", watch=True)
    def load_data(self):
        # avoid threading issue
        self.ct_files = self.radiograph_folder.value
        self.ob_files = self.openbeam.value
        self.dc_files = self.darkcurrent.value
        # extract the rotation angles from radiograph filenames
        self.omegas = np.array(list(map(self.get_angle_from_file, self.ct_files)))
        # get the image array
        self.ct = self.read_tiffs(self.radiograph_folder.value, "CT")
        self.ob = self.read_tiffs(self.openbeam.value, "OB")
        self.dc = self.read_tiffs(self.darkcurrent.value, "DC")
        #
        pn.state.notifications.success("Data lading complete.", duration=3000)

    def read_tiffs(self, filelist, desc):
        if len(filelist) == 0:
            return None
        data = []
        for me in self.progress_bar(filelist, desc=desc):
            data.append(tifffile.imread(me))
        return np.array(data)

    def get_angle_from_file(self, filename):
        """extract rotation angle in degrees"""
        return float(".".join(os.path.basename(filename).split("_")[4:6]))

    @param.output(
        ("ct", param.Array),
        ("ob", param.Array),
        ("dc", param.Array),
        ("omegas", param.Array),
        ("recn_root", param.Path),
        ("temp_root", param.Path),
        ("recn_name", param.String),
    )
    def output(self):
        return (
            self.ct,
            self.ob,
            self.dc,
            self.omegas,
            self.recn_root,
            self.temp_root,
            self.recn_name,
        )

    def panel(self):
        return pn.Column(
            pn.widgets.Button.from_param(
                self.param.load_data_action,
                name="Load All",
                width=80,
                button_type="primary",
            ),
            self.file_selector,
            self.progress_bar,
            sizing_mode="stretch_width",
        )
