#!/usr/bin/env python3
"""Assisted reconstruction window for iMars3D.

To test the assisted reconstruction window in as a standalone app in Jupyter, run:

import panel as pn
from imars3d.ui.assisted_window import AssistedWindow

pn.extension(
    "jsoneditor",
    nthreads=0,
    notifications=True,
)
assisted_window = AssistedWindow()
assisted_window  # or pn.panel(assisted_window) or assisted_window.show() or assisted_window.servable()
"""
import panel as pn
import param
from imars3d.ui.base_window import BaseWindow

logger = param.get_logger(__name__)


class AssistedWindow(BaseWindow):
    """Sub-app for assisted reconstruction."""

    def __init__(self, **params):
        super().__init__(**params)
        self._panel = pn.panel("**Assisted reconstruction window.**")

    def __panel__(self):
        return self._panel
