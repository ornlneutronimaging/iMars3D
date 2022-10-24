#!/usr/bin/env python3
"""Reconstruction viewer window for iMars3D.

To test the reconstruction viewer window in as a standalone app in Jupyter, run:

import panel as pn
from imars3d.ui.viewer_window import ViewerWindow

pn.extension(
    "vtk",  # for the 3D viewer
    "terminal",  # or the console
    "jsoneditor",  # for config viewer
    nthreads=0,
    notifications=True,
)
viewer_window = ViewerWindow()
viewer_window  # or pn.panel(viewer_window) or viewer_window.show() or viewer_window.servable()
"""
import logging
import panel as pn
import param
from pathlib import Path
from imars3d.ui.base_window import BaseWindow
from imars3d.backend.io.data import _load_images

logger = param.get_logger(__name__)


class ViewerWindow(BaseWindow):
    """Sub-app for reconstruction viewer."""

    # container
    recon = param.Array(doc="Reconstruction data as a 3D numpy array.")
    # load strip
    init_dir = param.Action(lambda x: x.param.trigger("init_dir"))
    dirs = param.Selector(doc="List of directories to search for data.")
    fnmatch = param.String(default="*.tiff", doc="File name pattern to match.")
    load_data = param.Action(lambda x: x.param.trigger("load_data"))
    # view strip
    view_type = param.Selector(
        default="3D",
        objects=[
            "3D",  # vtkvolume rendering without js control
            "3D with control",  # vtkvolume rendering with js control
            "2D",  # holoview 2D view along rotation axis (y-axis in beamline frame)
            "H-stack",  # orthogonal view (x-y, y-z, x-z)
        ],
    )
    # console strip
    log_lv = param.Selector(
        default=logging.INFO,
        objects=[logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL],
        doc="Log level.",
    )
    log_lv_str = param.Selector(
        default="INFO",
        objects=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        doc="Log level.",
    )

    def __init__(self, **params):
        #
        super().__init__(**params)
        #
        self.log_lv = logging.INFO
        #
        init_btn = pn.widgets.Button.from_param(
            self.param.init_dir,
            name="Init",
            button_type="primary",
            height=50,
            width=50,
        )
        #
        dir_selector = pn.widgets.Select.from_param(
            self.param.dirs,
            name="Select folder contains reconstruction data",
            options=self._get_list_of_dirs(),
        )
        fnmatch_input = pn.widgets.TextInput.from_param(
            self.param.fnmatch,
            name="File name pattern to match",
        )
        load_data_btn = pn.widgets.Button.from_param(
            self.param.load_data,
            name="Load",
            button_type="success",
            height=50,
            width=50,
        )
        load_control_pn = pn.Row(
            init_btn,
            dir_selector,
            fnmatch_input,
            load_data_btn,
        )
        #
        view_type_selector = pn.widgets.Select.from_param(
            self.param.view_type,
            name="View type",
        )
        viewer_pn = pn.Column(
            view_type_selector,
            self.viewer,
            sizing_mode="stretch_width",
        )
        #
        log_lv_selector = pn.widgets.RadioButtonGroup.from_param(
            self.param.log_lv_str,
            name="Log Level",
            height=30,
        )
        console_pn = pn.Column(
            self.log_console,
            log_lv_selector,
            sizing_mode="stretch_width",
        )
        #
        self._panel = pn.Column(
            load_control_pn,
            viewer_pn,
            console_pn,
        )

    def _get_list_of_dirs(self):
        """Return candidate dir list."""
        output_dir = self.config_dict.get("workingdir", None)
        if output_dir is None:
            return []
        else:
            return [str(p) for p in Path(output_dir).glob("**/")]

    @param.depends("load_data", watch=True)
    def load_data_action(self):
        """Load reconstruction data."""
        logger.info("Loading reconstruction data...")
        if self.dirs is None:
            logger.warning("No directory selected.")
        else:
            files = sorted(list(map(str, Path(self.dirs).glob(self.fnmatch))))
            # load images
            # NOTE: https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor
            #       without setting max_workers, it will use all available cores capped at 61.
            self.recon = _load_images(
                filelist=files,
                desc="Loading reconstruction data",
                max_workers=None,
            )

    @param.depends("init_dir", watch=True)
    def _update_dirs(self):
        """Update options in dir selector."""
        self.param.dirs.objects = self._get_list_of_dirs()

    @param.depends("view_type", "recon")
    def viewer(self):
        """Return viewer panel."""
        if self.recon is None:
            return pn.panel("No reconstruction data loaded.")
        if self.view_type == "3D":
            return self.viewer_3d
        elif self.view_type == "3D with control":
            return self.viewer_3d_with_control
        elif self.view_type == "2D":
            return pn.panel("2D viewer")
        elif self.view_type == "H-stack":
            return pn.panel("H-stack viewer")

    @param.depends("recon")
    def viewer_3d(self):
        """Return 3D viewer."""
        return pn.pane.VTKVolume(self.recon, sizing_mode="stretch_width", interpolation="nearest")

    @param.depends("recon")
    def viewer_3d_with_control(self):
        """Return 3D viewer."""
        vtk_model = pn.pane.VTKVolume(self.recon, sizing_mode="stretch_width", interpolation="nearest")
        return pn.Row(
            vtk_model.controls(jslink=True, width=200),
            vtk_model,
            sizing_mode="stretch_width",
        )

    @param.depends("log_lv_str", watch=True)
    def set_log_level(self):
        """Set log level.

        This callback is necessary because the representation of log level are
        integers, therefore the automated display cannot display the proper
        name.
        """
        if self.log_lv_str == "DEBUG":
            logger.debug("Switching to DEBUG log level.")
            self.log_lv = logging.DEBUG
        elif self.log_lv_str == "INFO":
            logger.info("Switching to INFO log level.")
            self.log_lv = logging.INFO
        elif self.log_lv_str == "WARNING":
            logger.warning("Switching to WARNING log level.")
            self.log_lv = logging.WARNING
        elif self.log_lv_str == "ERROR":
            logger.error("Switching to ERROR log level.")
            self.log_lv = logging.ERROR
        elif self.log_lv_str == "CRITICAL":
            logger.critical("Switching to CRITICAL log level.")
            self.log_lv = logging.CRITICAL

    def get_imars3d_loggers(self):
        """Return a list of iMars3D loggers."""
        return [name for name in logging.root.manager.loggerDict if "imars3d" in name]

    @param.depends("log_lv")
    def log_console(self):
        """Log console."""
        return pn.widgets.Debugger(
            name="Console",
            level=self.log_lv,
            sizing_mode="stretch_width",
            logger_names=["panel", "imars3d"],
        )

    def __panel__(self):
        return self._panel


if __name__ == "__main__":
    pn.extension(
        "vtk",  # for the 3D viewer
        "terminal",  # or the console
        "jsoneditor",  # for config viewer
        nthreads=0,
        notifications=True,
    )
    viewer_window = ViewerWindow()
