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
import json
import sys
from imars3d.ui.base_window import BaseWindow
from imars3d.backend.workflow.engine import WorkflowEngineAuto

import logging


logger = logging.getLogger(__name__)

class AssistedWindow(BaseWindow):
    """Sub-app for assisted reconstruction."""
    
    log_level_str = param.Selector(
        default="INFO", 
        objects=["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"],
        doc="Level of logging in the console."
    )
    
    log_level = param.Selector(
        default=logging.INFO,
        objects=[logging.INFO, logging.DEBUG, logging.WARNING, logging.ERROR, logging.CRITICAL],
        doc="Level of logging in the console."
    )
    
    file_input = pn.widgets.FileInput(
            accept='.json'
    )
    
    def __init__(self, **params):
        super().__init__(**params)

        self.log_level = logging.INFO
        self.go_button = pn.widgets.Button(
            name='GO', 
            button_type='primary',
            width=100
        )
        self.go_button.on_click(self.launch_assisted_reconstruction)
        
        self.log_level_radio = pn.widgets.RadioButtonGroup.from_param(
             self.param.log_level_str,
             name="Debugger Level",
             tooltips="Select debugger level",      
        )
        
        self.console = pn.widgets.Debugger(
            name='Debugger', 
            level=self.log_level, 
            sizing_mode='stretch_width',
            logger_names=["panel", "imars3d"],
        )
        left_column = pn.Column(self.go_button, self.log_level_radio, self.console, sizing_mode='stretch_both')
        right_column = pn.Column(self.json_editor(), self.file_input, sizing_mode='stretch_both')
        self._panel = pn.Row(left_column, right_column)

    @param.depends('log_level_str', watch=True)
    def set_log_level(self):
        self.log_level = logging.getLevelName(self.log_level_str)
        logging.getLogger("imars3d").setLevel(self.log_level)
        logger.log(self.log_level, f"Switching to {self.log_level_str} log level.")
        
    @param.depends("file_input.value", watch=True) 
    def update_config_dict(self):
        logger.info("Updating config dict with uploaded json file.")
        new_config_dict = json.loads(self.file_input.value)
        try:
            # Validating new config file by instantiating WorkflowEngineAuto
            validate_dict = WorkflowEngineAuto(new_config_dict)
            self.config_dict = new_config_dict
        except:
            log.error("Could not update config file. Reverting to previous config.")
   
    def launch_assisted_reconstruction(self, event): 
        logger.info('Launching assisted reconstruction.')
        wfEngine = WorkflowEngineAuto(self.config_dict)
        wfEngine.run()