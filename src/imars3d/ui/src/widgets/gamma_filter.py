#!/usr/bin/env python3

import param
import panel as pn
from imars3d.backend.corrections.gamma_filter import gamma_filter


class GammaFilter(param.Parameterized):
    """
    Widget for the gamma filter from iMars3D, must have a parent widget with
    validate ct stack.
    """

    parent = param.Parameter(doc="parent widget holding the data")
    #
    auto_threshold = param.Boolean(default=True, doc="use internal default saturation threshold")
    threshold = param.Integer(default=65530, doc="threshold for saturation")
    median_kernel = param.Integer(default=5, bounds=(3, None), doc="size of the median filter kernel")
    axis = param.Integer(default=0, bounds=(0, 2), doc="axis for parallel computing")
    selective_median_filter = param.Boolean(default=True, doc="whether to use selective median filtering")
    auto_tomopy_threshold = param.Boolean(default=True, doc="whether to use default threshold for tomopy.median")
    tomopy_threshold = param.Number(default=13107, bounds=(1, None), doc="threshold for tomopy median")
    #
    execute = param.Action(lambda x: x.param.trigger("execute"), label="Execute")
    status = param.Boolean(default=False, doc="IFC completion status")

    @param.depends("execute", watch=True)
    def apply(self):
        if self.parent.ct is None:
            pn.state.notifications.warning("no CT found", duration=3000)
        else:
            # call the filter
            threshold = -1 if self.auto_threshold else self.threshold
            tomopy_threshold = -1 if self.auto_tomopy_threshold else self.tomopy_threshold
            self.parent.ct = gamma_filter(
                arrays=self.parent.ct,
                threshold=threshold,
                median_kernel=self.median_kernel,
                axis=self.axis,
                selective_median_filter=self.selective_median_filter,
                diff_tomopy=tomopy_threshold,
            ).astype(self.parent.ct.dtype)
            #
            self.status = True
            pn.state.notifications.success("gamma filtering complete.", duration=3000)

    def panel(self, width=200):
        # use selective median filter
        selective_median_filter = pn.widgets.Toggle.from_param(
            self.param.selective_median_filter,
            name="Use selective median",
            width=width,
        )
        # threshold
        auto_threshold = pn.widgets.Checkbox.from_param(
            self.param.auto_threshold,
            name="auto",
        )
        threshold = pn.widgets.IntInput.from_param(
            self.param.threshold,
            name="",
            width=int(width / 2.5),
            disabled=self.auto_threshold,
        )
        threshold_pn = pn.WidgetBox(
            "Threshold",
            auto_threshold,
            threshold,
            width=width // 2,
        )
        # tomopy threshold
        auto_tomopy_threshold = pn.widgets.Checkbox.from_param(
            self.param.auto_tomopy_threshold,
            name="auto",
        )
        tomopy_threshold = pn.widgets.IntInput.from_param(
            self.param.tomopy_threshold,
            name="",
            width=int(width / 2.5),
            disabled=self.auto_tomopy_threshold,
        )
        tomopy_threshold_pn = pn.WidgetBox(
            "TomopyDiff",
            auto_tomopy_threshold,
            tomopy_threshold,
            width=width // 2,
        )
        #
        median_kernel = pn.widgets.IntInput.from_param(
            self.param.median_kernel,
            name="median kernel",
            width=int(width / 2.2),
        )
        #
        axis = pn.widgets.IntInput.from_param(
            self.param.axis,
            name="axis",
            width=int(width / 2.2),
        )
        # execut
        status_indicator = pn.widgets.BooleanStatus.from_param(
            self.param.status,
            color="success",
        )
        execute_button = pn.widgets.Button.from_param(
            self.param.execute,
            width=width // 2,
        )
        execute_pn = pn.Row(
            status_indicator,
            execute_button,
            width=width,
        )
        #
        app = pn.Column(
            selective_median_filter,
            pn.Row(threshold_pn, tomopy_threshold_pn),
            pn.Row(median_kernel, axis),
            execute_pn,
            width=width,
        )
        return app
