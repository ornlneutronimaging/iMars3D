#!/usr/bin/env python3
"""Main window for iMars3D GUI.

To test the main window in as a standalone app in Jupyter, run:

import panel as pn
from imars3d.ui.main import MainWindow

pn.extension(
    "vtk",  # for the 3D viewer
    "terminal",  # or the console
    "jsoneditor",  # for config viewer
    nthreads=0,
    notifications=True,
)
main_window = MainWindow()
main_window  # or pn.panel(main_window) or main_window.show() or main_window.servable()
"""
import logging
import panel as pn
import param
from imars3d.ui.base_window import BaseWindow
from imars3d.ui.welcome_window import WelcomeWindow
from imars3d.ui.interactive_window import InteractiveWindow
from imars3d.ui.assisted_window import AssistedWindow
from imars3d.ui.viewer_window import ViewerWindow

logger = logging.getLogger(__name__)


class MainWindow(BaseWindow):
    """Main application to handle all logics"""

    # component window (sub-app)
    welcome_window = param.ClassSelector(class_=WelcomeWindow)
    interactive_window = param.ClassSelector(class_=InteractiveWindow)
    assisted_window = param.ClassSelector(class_=AssistedWindow)
    viewer_window = param.ClassSelector(class_=ViewerWindow)
    # actions
    start_imars3d = param.Action(lambda x: x.param.trigger("start_imars3d"))

    def __init__(self, **params):
        if "welcome_window" not in params:
            params["welcome_window"] = WelcomeWindow()
        if "interactive_window" not in params:
            params["interactive_window"] = InteractiveWindow()
        if "assisted_window" not in params:
            params["assisted_window"] = AssistedWindow()
        if "viewer_window" not in params:
            params["viewer_window"] = ViewerWindow()

        super().__init__(**params)

        self.welcome_window.config_dict = self.config_dict
        self.interactive_window.config_dict = self.config_dict
        self.assisted_window.config_dict = self.config_dict
        self.viewer_window.config_dict = self.config_dict

        # start out with the welcome to collect metadata
        self._panel = self.welcome_page()

    @param.depends("welcome_window.is_valid")
    def go_to_app_button(self):
        return pn.widgets.Button.from_param(
            self.param.start_imars3d,
            name="Go to iMars3D",
            button_type="success",
            width=80,
            disabled=not self.welcome_window.is_valid,
        )

    @param.depends("start_imars3d", watch=True)
    def start_imars3d_action(self):
        """Callback for start_imars3d."""
        self._panel = self.app_page()

    def welcome_page(self):
        """Return the welcome page."""
        return pn.Column(self.welcome_window, self.go_to_app_button)

    def app_page(self):
        """Return the main app view."""
        return pn.Tabs(
            ("Interactive", self.interactive_window),
            ("Assisted", self.assisted_window),
            ("Visualization", self.viewer_window),
            tabs_location="left",
        )

    def __panel__(self):
        """Return the main app view."""
        return self._panel
