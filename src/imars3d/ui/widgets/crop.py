#!/usr/bin/env python3
"""Crop widget for iMars3D.

To test this widget in isolation within Jupyter, do the following:

    import panel as pn
    import holoviews as hv
    from imars3d.ui.widgets.crop import CropWidget

    pn.extension()
    hv.extension('bokeh')

    crop_widget = CropWidget()
    # manual update the embedded config to make sure the load task
    # has valid entries as we will be using those to test the widget.
    crop_widget.config_dict["tasks"] = [
        {
            "name": "load",
            "function": "imars3d.backend.io.data.load_data",
            "inputs": {
                "ct_dir": "/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man",
                "ob_dir": "/HFIR/CG1D/IPTS-25777/raw/ob/Oct29_2019/",
                "dc_dir": "/HFIR/CG1D/IPTS-25777/raw/df/Oct29_2019/",
                "ct_fnmatch": "*.tiff",
                "ob_fnmatch": "*.tiff",
                "dc_fnmatch": "*.tiff"
            },
            "outputs": ["ct", "ob", "dc", "rot_angles"]
        }
    ]

    crop_widget  # or pn.panel(viewer_window) or viewer_window.show() or viewer_window.servable()

    }
"""
import logging
import param
import numpy as np
import panel as pn
import holoviews as hv
from holoviews import opts
from holoviews import streams
from imars3d.ui.base_window import BaseWindow
from imars3d.ui.widgets.viewer2d import Viewer2D
from imars3d.backend.morph.crop import crop
from imars3d.ui.util import run_task

logger = logging.getLogger(__name__)


class CropWidget(BaseWindow, Viewer2D):
    """Crop widget to allow user specify crop region in interactively."""

    # toggles
    show_advanced = param.Boolean(
        default=False,
        doc="whether to display advaned options with predence less than 0.5.",
    )
    crop_darkcurrent = param.Boolean(
        default=True,
        doc="if dark currents are used, it must be cropped here.",
    )
    # load data button
    load_data = param.Action(lambda x: x.param.trigger("load_data"))
    record_roi = param.Action(lambda x: x.param.trigger("record_roi"))
    #
    roi_box = hv.Polygons([])
    roi_box_stream = streams.BoxEdit()

    def __init__(self, data=None, **params):
        super().__init__(data=data, **params)

        self.func_name = f"{crop.__module__}.crop"

        # func panel
        # NOTE:
        #   1. the functional panel is directly translated from the function signature.
        #   2. the input arrays/ct/ob/dc are masked with precedence=-1 so that they don't
        #      show up in the GUI
        #   3. the value retrieving is done via simple name matching.
        self.func_panel = pn.Param(
            crop,
            display_threshold=0.6,  # default to hide advanced options
        )
        show_advanced_checkbox = pn.widgets.Checkbox.from_param(
            self.param.show_advanced,
            name="Advanced Options",
        )
        crop_darkcurrent_checkbox = pn.widgets.Checkbox.from_param(
            self.param.crop_darkcurrent,
            name="Crop DarkCurrent",
        )
        #
        func_pn = pn.Column(
            self.func_panel,
            crop_darkcurrent_checkbox,
            show_advanced_checkbox,
        )

        # viewer pane
        load_data_button = pn.widgets.Button.from_param(
            self.param.load_data,
            name="Load projected radiographs",
        )
        #
        view_pn = pn.Column(
            load_data_button,
            pn.Row(
                self.view_control_panel,
                self.viewer,
                sizing_mode="stretch_width",
            ),
        )

        # complete view
        self._panel = pn.Row(func_pn, view_pn)

        # trigger update in case data is set during init
        self.data = data

    @param.depends("load_data", watch=True)
    def load_data_action(self):
        logger.info("Start loading data")
        # looking for load function in config_dict
        tasks = self.config_dict["tasks"]
        load_task = None
        for task in tasks:
            if task["function"] == "imars3d.backend.io.data.load_data":
                load_task = task
                break
        # process load task
        if load_task is None:
            logger.warning("No task entry for loading data.")
        else:
            mtd = {}
            run_task(mtd, task=load_task)
            self.data = np.sum(mtd["ct"], axis=0)
            mtd.clear()

    @param.depends(
        "data",
        "idx_data",
        "colormap",
        "colormap_scale",
    )
    def viewer(self):
        if self.data is None:
            return pn.panel("No radiograph loaded.")
        else:
            img = hv.Image(
                (
                    np.arange(self.data.shape[1]),
                    np.arange(self.data.shape[0]),
                    self.data,
                ),
                kdims=["x", "y"],
                vdims=["count"],
            )
            self.roi_box_stream = streams.BoxEdit(source=self.roi_box, num_objects=1)
            #
            def update_roi(data):
                """Internal function.

                This function tricks Bokeh into updating the crop panel limit whenever
                a valid ROI selection is provided.
                """
                try:
                    top = int(data["y1"][0])
                    bottom = int(data["y0"][0])
                    left = int(data["x0"][0])
                    right = int(data["x1"][0])
                    self.update_crop_limit(top, bottom, left, right)
                    return hv.Text(0, -10, "Trick bokeh to update ROI.")
                except:
                    logger.debug("no ROI found.")
                    return hv.Text(0, -10, "Trick bokeh to update ROI.")

            dmap = hv.DynamicMap(update_roi, streams=[self.roi_box_stream])
            #
            return (img.hist() * self.roi_box * dmap).opts(
                opts.Image(
                    tools=["hover"],
                    cmap=self.colormap,
                    cnorm=self.colormap_scale,
                    data_aspect=1.0,
                    invert_yaxis=True,
                    xaxis=None,
                    yaxis=None,
                ),
                opts.Polygons(
                    fill_alpha=0.2,
                    line_color="red",
                ),
            )

    def update_crop_limit(self, top, bottom, left, right):
        """Update the crop limit in the function panel."""
        for w in self.func_panel:
            if w.name.lower().replace(" ", "_") == "crop_limit":
                w.value = (top, bottom, left, right)

    @param.depends("show_advanced", watch=True)
    def _update_advance_options(self):
        if self.show_advanced:
            logger.debug("Advanced option on.")
            self.func_panel.display_threshold = 0.0
        else:
            logger.debug("Advanced option off.")
            self.func_panel.display_threshold = 0.6

    def get_task_list(self):
        """Translate the values from widget."""
        # grab values from panel widget
        param_dict_shared = {
            widget.name.lower().replace(" ", "_"): widget.value for widget in self.func_panel if widget.name != ""
        }

        # crop ct
        param_dict_ct = {"array": "ct"}
        param_dict_ct.update(param_dict_shared)
        task_crop_ct = {
            "name": "crop radiographs",
            "function": self.func_name,
            "inputs": param_dict_ct,
            "outputs": ["ct"],
        }

        # crop ob
        param_dict_ob = {"array": "ob"}
        param_dict_ob.update(param_dict_shared)
        task_crop_ob = {
            "name": "crop open beams",
            "function": self.func_name,
            "inputs": param_dict_ob,
            "outputs": ["ob"],
        }

        # crop dc
        if self.crop_darkcurrent:
            param_dict_dc = {"array": "dc"}
            param_dict_dc.update(param_dict_shared)
            task_crop_dc = {
                "name": "crop dark currents",
                "function": self.func_name,
                "inputs": param_dict_dc,
                "outputs": ["dc"],
            }
        else:
            task_crop_dc = None

        return [
            task_crop_ct,
            task_crop_ob,
            task_crop_dc,
        ]

    def __panel__(self):
        return self._panel


if __name__ == "__main__":
    import panel as pn
    import holoviews as hv
    from imars3d.ui.widgets.crop import CropWidget

    pn.extension()
    hv.extension("bokeh")

    crop_widget = CropWidget()
