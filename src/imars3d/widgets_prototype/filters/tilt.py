#!/usr/bin/env python3

import param
import panel as pn
import numpy as np
from imars3d.filters.tilt import tilt_correction


class TiltCorrection(param.Parameterized):
    """
    Widget for tilt correction from iMars3D, must have parent widget with valid
    ct stack.
    """

    #
    parent = param.Parameter()
    #
    tilt_search_bounds = param.Range(default=(-5.0, 5.0), doc="tilt angle search range")
    cut_off_angle_deg = param.Number(default=1e-3, doc="ignore tilt angle below this value")
    #
    execute = param.Action(lambda x: x.param.trigger("execute"), label="Execute")
    status = param.Boolean(default=False, doc="IFC completion status")

    @param.depends("execute", watch=True)
    def apply(self):
        if self.parent.ct is None:
            pn.state.notifications.warning("no CT found", duration=3000)
        else:
            # perform tilt correction
            self.parent.ct = tilt_correction(
                arrays=self.parent.ct,
                omegas=np.radians(self.parent.omegas),
                low_bound=self.tilt_search_bounds[0],
                high_bound=self.tilt_search_bounds[1],
                cut_off_angle_deg=self.cut_off_angle_deg,
            )
            #
            self.status = True
            #
            pn.state.notifications.success("Tilt correction complete.", duration=3000)

    def panel(self, width=200):
        #
        tilt_search_bounds_input = pn.widgets.LiteralInput.from_param(
            self.param.tilt_search_bounds,
            name="tilt search range (deg)",
        )
        cutoff_angle_input = pn.widgets.LiteralInput.from_param(
            self.param.cut_off_angle_deg,
            name="cutoff tilt angle (deg)",
        )
        #
        status_indicator = pn.widgets.BooleanStatus.from_param(
            self.param.status,
            color="success",
        )
        execute_button = pn.widgets.Button.from_param(
            self.param.execute,
            width=width // 2,
        )
        #
        app = pn.Column(
            tilt_search_bounds_input,
            cutoff_angle_input,
            pn.Row(status_indicator, execute_button, width=width),
            width=width,
        )
        return app
