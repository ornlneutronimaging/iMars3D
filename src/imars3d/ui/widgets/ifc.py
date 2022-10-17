#!/usr/bin/env python3
"""Widgets for intensity fluctuation correction."""
import param
import panel as pn
from imars3d.backend.corrections.intensity_fluctuation_correction import intensity_fluctuation_correction


class IntensityFluctuationCorrection(param.Parameterized):
    """IFC widget.

    Widget for the intensity fluctuation correction filter from iMars3D, must have a
    parent with valid ct stack.
    """

    #
    parent = param.Parameter()
    #
    air_pixels = param.Integer(
        default=5,
        bounds=(1, None),
        doc="Number of pixels at each boundary to calculate the scaling factor.",
    )
    auto_detect_air = param.Boolean(
        default=False,
        doc="whether to use auto air region detection instead of specifying air pixels",
    )
    sigma = param.Integer(
        default=3, bounds=(3, None), doc="The standard deviation of the Gaussian filter during auto detection"
    )
    #
    execute = param.Action(lambda x: x.param.trigger("execute"), label="Execute")
    status = param.Boolean(default=False, doc="IFC completion status")

    @param.depends("execute", watch=True)
    def apply(self):
        """Apply IFC."""
        if self.parent.ct is None:
            pn.state.notifications.warning("no CT found", duration=3000)
        else:
            # auto detect air?
            if self.auto_detect_air:
                self.parent.ct = intensity_fluctuation_correction(
                    arrays=self.parent.ct,
                    air_pixels=-1,  # use negative value to trigger auto detection
                    sigma=self.sigma,
                )
            else:
                self.parent.ct = intensity_fluctuation_correction(
                    arrays=self.parent.ct,
                    air_pixels=self.air_pixels,
                )
            #
            self.status = True
            pn.state.notifications.success("IFC complete.", duration=3000)

    def panel(self, width=200):
        """App card view."""
        #
        auto_air_toggle = pn.widgets.Toggle.from_param(
            self.param.auto_detect_air,
            name="Auto Air Detection",
        )
        air_pixel_input = pn.widgets.IntInput.from_param(
            self.param.air_pixels,
            name="Air pixels",
        )
        sigma_input = pn.widgets.IntInput.from_param(
            self.param.sigma,
            name="sigma",
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
        if self.auto_detect_air:
            app = pn.Column(
                auto_air_toggle,
                sigma_input,
                pn.Row(status_indicator, execute_button, width=width),
                width=width,
            )
        else:
            app = pn.Column(
                auto_air_toggle,
                air_pixel_input,
                pn.Row(status_indicator, execute_button, width=width),
                width=width,
            )
        return app
