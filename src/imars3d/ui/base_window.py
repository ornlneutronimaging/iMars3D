#!/usr/bin/env python3
"""Base window class for developing pages for iMars3D GUI.

To test the base window in as a standalone app in Jupyter, run:

import panel as pn
from imars3d.ui.base_window import BaseWindow

pn.extension(
    "jsoneditor",
    nthreads=0,
    notifications=True,
)
base_window = BaseWindow()
base_window  # or pn.panel(base_window) or base_window.show() or base_window.servable()
"""
import panel as pn
import param


class BaseWindow(pn.viewable.Viewer):
    """Base class for all viewer."""

    # configuration
    config_dict = param.Dict(
        default={
            "facility": "TBD",
            "instrument": "TBD",
            "ipts": "IPTS-00000",
            "name": "TBD",
            "workingdir": "TBD",
            "outputdir": "TBD",
            "tasks": [],
        },
        doc="Configuration dictionary",
    )

    def __init__(self, **params):
        super().__init__(**params)
        self._panel = self.json_editor

    @param.output(
        ("config_dict", param.Dict),
    )
    def as_dict(self):
        """Return config dict."""
        return self.config_dict

    @param.depends("config_dict", on_init=True)
    def json_editor(self):
        """Return a json editor pane."""
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

    def __panel__(self):
        """Return the panel this is associated with."""
        return self._panel
