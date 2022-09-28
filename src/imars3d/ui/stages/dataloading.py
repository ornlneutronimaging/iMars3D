#!/usr/bin/env python3
"""
Data loading stage for iMars3D
"""
from pathlib import Path
import param
import panel as pn
from imars3d.backend.io.config import save_config


class DataLoader(param.Parameterized):
    # take over config from previous step
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
        },
        doc="Configuration dictionary",
    )
    # button to write filelist to json
    update_config_action = param.Action(lambda x: x.param.trigger("update_config_action"))
    save_config_to_disk = param.Action(lambda x: x.param.trigger("save_config_to_disk"))

    @param.depends("save_config_to_disk", watch=True)
    def save_config_file(self):
        wkdir = Path(self.config_dict["outputdir"])
        config_filename = str(wkdir / f"{self.config_dict['name']}.json")
        save_config(self.config_dict, config_filename)

    @param.depends("update_config_action", watch=True)
    def update_config(self):
        # NOTE:
        # the filter name get be get by
        # left search bar entry: dataloader.radiograph_folder._selector._search[False].value
        # right search bar entry: dataloader.radiograph_folder._selector._search[True].value
        #
        # NOTE:
        # when a user is using the GUI to generate the list, it should include all the files,
        # therefore no need for additional filtering by setting *_dc_fnmatch
        #
        # NOTE:
        # it is better to hide the control of how many cores to use from user, hence using the
        # default values for max_workers (by not setting one here).
        load_step = {
            "name": "load",
            "version": 1,  # where does this version come from?
            "inputs": {
                "ct_files": self.radiograph_folder.value,
                "ob_files": self.openbeam.value,
                "dc_files": self.darkcurrent.value,
            },
            "outputs": ["ct", "ob", "dc", "rot_angles"],
        }
        self.config_dict["steps"].append(load_step)

    @param.depends("config_dict")
    def file_selector(self):
        # use user home directory if invalid one found in config file
        prjdir = str(Path.home())
        if self.config_dict["projectdir"] != "TBD":
            prjdir = self.config_dict["projectdir"]
        #
        self.radiograph_folder = pn.widgets.FileSelector(
            directory=prjdir,
            name="Radiographs(CT)",
        )
        self.openbeam = pn.widgets.FileSelector(
            directory=prjdir,
            name="Open-beam(OB)",
        )
        self.darkcurrent = pn.widgets.FileSelector(
            directory=prjdir,
            name="Dark-current(DC)",
        )
        return pn.Tabs(self.radiograph_folder, self.openbeam, self.darkcurrent)

    @param.output(
        ("config_dict", param.Dict),
    )
    def as_dict(self):
        return self.config_dict

    @param.depends("config_dict")
    def json_editor(self):
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
        return config_viewer

    def panel(self):
        save_json_button = pn.widgets.Button.from_param(self.param.save_config_to_disk, name="Save Config")
        update_config_button = pn.widgets.Button.from_param(self.param.update_config_action, name="Update Config")
        buttons = pn.Row(update_config_button, save_json_button)
        return pn.Column(
            buttons,
            self.file_selector,
            self.json_editor,
            sizing_mode="stretch_width",
        )
