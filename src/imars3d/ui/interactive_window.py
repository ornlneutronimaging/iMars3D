#!/usr/bin/env python3
"""Interactive reconstruction window for iMars3D.

To test the interactive reconstruction window in as a standalone app in Jupyter, run:

import panel as pn
from imars3d.ui.interactive_window import InteractiveWindow

pn.extension(
    "jsoneditor",
    nthreads=0,
    notifications=True,
)
interactive_window = InteractiveWindow()
interactive_window  # or pn.panel(interactive_window) or interactive_window.show() or interactive_window.servable()
"""
import logging
import panel as pn
import param
from imars3d.ui.base_window import BaseWindow

logger = logging.getLogger(__name__)


class InteractiveWindow(BaseWindow):
    """Sub-app for interactive reconstruction."""

    def __init__(self, **params):
        super().__init__(**params)
        self._panel = pn.panel("**Interactive reconstruction window.**")

    def __panel__(self):
        return self._panel
