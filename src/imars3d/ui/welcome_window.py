#!/usr/bin/env python3
"""Welcome page for iMars3D GUI.

To test the welcome page in as a standalone app in Jupyter, run:

import panel as pn
from imars3d.ui.welcome_window import WelcomeWindow

pn.extension(
    "jsoneditor",
    nthreads=0,
    notifications=True,
)

welcome_window = WelcomeWindow()
welcome_window  # or pn.panel(welcome_window) or welcome_window.show() or welcome_window.servable()
"""
import logging
import panel as pn
import param
from pathlib import Path
from imars3d.ui.base_window import BaseWindow

logger = logging.getLogger(__name__)


class WelcomeWindow(BaseWindow):
    """Welcome window.

    The main purpose of this window is to force users to provide the following information:
    - Instrument
    - IPTS number
    - Name of the experiment

    and the window will auto update the following fields
    - working directory
    - output directory
    """

    # basic input
    instrument = param.Selector(
        default="CG1D",
        objects=[
            "CG1D",
            "SNAP",
            # "VENUS", "CUPID",  # these are future instruments
        ],
        doc="name of neutron imaging instrument",
    )
    facility = param.String(default="HFIR", doc="hosting facility of instrument")
    ipts_num = param.Integer(
        default=0,
        bounds=(0, None),
        doc="IPTS number",
    )
    recon_name = param.String(default="recon", doc="name of the reconstruction")
    # derived input fields
    working_dir = param.String(default=None, doc="Folder that holds all intermediate results.")
    output_dir = param.String(default=None, doc="Folder that holds the final reconstruction results.")
    # flags
    is_valid = param.Boolean(default=False, doc="control if users can ")

    def __init__(self, **params):
        super().__init__(**params)
        #
        self._panel = pn.panel("WelcomeWindow")

    @param.depends("instrument", watch=True)
    def _update_facility(self):
        if self.instrument in ("CG1D"):
            self.facility = "HFIR"
        elif self.instrument in ("SNAP", "VENUS"):
            self.facility = "SNS"
        elif self.instrument in ("CUPID"):
            self.facility = "STS"
        else:
            logger.error(f"Unknown instrument: {self.instrument}")
            pn.state.notifications.error("Unknown instrument", duration=1000)

    @param.depends("instrument", "ipts_num", "recon_name", watch=True)
    def _update_dirs(self):
        """update working directory and output directory"""
        project_root = Path(f"/{self.facility}/{self.instrument}/IPTS-{self.ipts_num}")
        if project_root.exists():
            working_dir = project_root / Path(f"shared/processed_data/{self.recon_name}")
            output_dir = working_dir / Path("reconstruction")
            # manage dir for saving intermediate data
            if working_dir.exists():
                logger.warning(f"setting an existing dir as working dir: {working_dir}")
            else:
                working_dir.mkdir()
            # manage dir for saving final reconstruction
            output_dir = working_dir / Path("reconstruction")
            if working_dir.exists():
                logger.warning(f"using existing dir to save reconstruction: {output_dir}")
            else:
                output_dir.mkdir()
            # update member
            self.working_dir, self.output_dir = str(working_dir), str(output_dir)
            # update flag
            self.is_valid = True
        else:
            pn.state.notifications.warning(f"{project_root} does not exist.", duration=1000)
            self.is_valid = False

    @param.depends("working_dir", "output_dir", watch=True)
    def _update_config(self):
        self.config_dict["facility"] = self.facility
        self.config_dict["instrument"] = self.instrument
        self.config_dict["ipts"] = f"IPTS-{self.ipts_num}"
        self.config_dict["name"] = self.recon_name
        self.config_dict["workingdir"] = str(self.working_dir)
        self.config_dict["outputdir"] = str(self.output_dir)

    @param.depends("instrument", "ipts_num", "recon_name")
    def _guide_pane(self):
        return pn.panel(
            f"""
        # Summary for reconstruction: {self.recon_name}

        | Category | Information |
        | -------- | ------ |
        | Instrument | {self.instrument}@{self.facility} |
        | Working directory | {self.working_dir} |
        | Results directory | {self.output_dir} |

        - configuration file will be saved to the working directory during interactive session.
        - the configuration file used to perform reconstruction will be cached in results dir, along with the reconstruction results.

        > If the information is correct, press the green button below to enter iMars3D.
        """,
            sizing_mode="stretch_width",
        )

    def __panel__(self):
        """Build and return the view for the welcome page."""
        # UI elements
        inst_input = pn.widgets.Select.from_param(
            self.param.instrument,
            name="Instrument",
            tooltips="Select instrument",
        )
        ipts_input = pn.widgets.LiteralInput.from_param(
            self.param.ipts_num,
            name="IPTS",
            tooltips="Enter IPTS number",
        )
        name_input = pn.widgets.TextInput.from_param(
            self.param.recon_name,
            name="Name",
            tooltips="Name for reconstruction",
        )
        # construct the view
        input_pn = pn.Row(inst_input, ipts_input, name_input)
        self._panel = pn.Column(input_pn, self._guide_pane)
        return self._panel
