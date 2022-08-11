#!/usr/bin/env python3

import param
import panel as pn
from imars3dv2.filters.denoise import denoise


class Denoise(param.Parameterized):
    """
    Widget for the denoise filter from iMars3D.
    """

    # container to store images
    ct = param.Array(
        doc="radiograph stack as numpy array",
        precedence=-1,  # hide
    )
    # denoise
    denoise_action = param.Action(lambda x: x.param.trigger("denoise_action"), label="Execute")
    denoise_method = param.Selector(default="bilateral", objects=["bilateral", "median"], doc="denoise method")
    denoise_median_kernel = param.Integer(
        default=3,
        bounds=(3, None),
        doc="The kernel size of the median filter",
    )
    denoise_bilateral_sigma_color = param.Number(
        default=0.02,
        bounds=(0, 1.0),
        doc="The sigma of the color/gray space for bilateral denoiser",
    )
    denoise_bilateral_sigma_spatial = param.Number(
        default=5,
        bounds=(0, None),
        doc="The sigma of the color/gray space for bilateral denoiser",
    )
    denoise_complete_status = param.Boolean(default=False, doc="CT is denoised.")

    @param.depends("denoise_action", watch=True)
    def apply(self):
        self.ct = denoise(
            arrays=self.ct,
            method=self.denoise_method,
            median_filter_kernel=self.denoise_median_kernel,
            bilateral_sigma_color=self.denoise_bilateral_sigma_color,
            bilateral_sigma_spatial=self.denoise_bilateral_sigma_spatial,
        )
        self.denoise_complete_status = True
        pn.state.notifications.success("Denoise complete.", duration=3000)

    @param.depends("denoise_method", "denoise_complete_status")
    def panel(self, width=200):
        #
        method_selector = pn.widgets.RadioButtonGroup.from_param(self.param.denoise_method)
        #
        meidan_kernel_input = pn.widgets.IntInput.from_param(
            self.param.denoise_median_kernel,
            name="kernel size",
        )
        #
        sigma_color_input = pn.widgets.FloatInput.from_param(
            self.param.denoise_bilateral_sigma_color,
            name="σ color",
            step=0.01,
        )
        sigma_spatial_input = pn.widgets.FloatInput.from_param(
            self.param.denoise_bilateral_sigma_spatial,
            name="σ spatial",
            step=0.1,
        )
        #
        denoise_status = pn.widgets.BooleanStatus.from_param(
            self.param.denoise_complete_status,
            color="success",
        )
        denoise_button = pn.widgets.Button.from_param(
            self.param.denoise_action,
            width=width // 2,
        )
        exec_pn = pn.Row(denoise_status, denoise_button, width=width)
        #
        if self.denoise_method == "median":
            app = pn.Card(
                method_selector,
                meidan_kernel_input,
                exec_pn,
                header="**Denoise**",
                collapsible=True,
                width=width,
            )
        else:
            app = pn.Card(
                method_selector,
                pn.Row(sigma_color_input, sigma_spatial_input, width=width),
                exec_pn,
                header="**Denoise**",
                collapsible=True,
                width=width,
            )
        return app
