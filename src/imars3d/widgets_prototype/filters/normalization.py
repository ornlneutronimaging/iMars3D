#!/usr/bin/env python3

import param
import panel as pn
from imars3d.filters.normalization import normalization


class Normalization(param.Parameterized):
    """
    Widget for the normalization filter from iMars3D, must have a parent widget with
    validate ct, ob, dc stack.
    """

    parent = param.Parameter(doc="parent widget holding the data")
    #
    auto_cutoff = param.Boolean(default=True, doc="Whether to use auto cutoff from tomopy.")
    cutoff = param.Number(default=1.0, doc="Permitted maximum vaue for the normalized data.")
    #
    execute = param.Action(lambda x: x.param.trigger("execute"), label="Execute")
    status = param.Boolean(default=False, doc="IFC completion status")

    @param.depends("execute", watch=True)
    def apply(self):
        if self.parent.ct is None:
            pn.state.notifications.warning("no CT found", duration=3000)
            return

        if self.parent.ob is None:
            pn.state.notifications.warning("no OB found", duration=3000)
            return

        if self.parent.dc is None:
            pn.state.notifications.warning("no DC found", duration=3000)
            return

        # call the filter
        cutoff = -1.0 if self.auto_cutoff else self.cutoff
        self.parent.ct = normalization(
            arrays=self.parent.ct,
            flats=self.parent.ob,
            darks=self.parent.dc,
            cut_off=cutoff,
        )
        #
        self.status = True
        pn.state.notifications.success("normalization complete.", duration=3000)

    def panel(self, width=200):
        # cutoff
        auto_cutoff = pn.widgets.Checkbox.from_param(
            self.param.auto_cutoff,
            name="auto",
        )
        cutoff = pn.widgets.FloatInput.from_param(
            self.param.cutoff,
            name="",
            width=int(width / 3),
            disabled=self.auto_cutoff,
        )
        cutoff_pn = pn.WidgetBox(
            "Cutoff",
            auto_cutoff,
            cutoff,
            width=width // 2,
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
            cutoff_pn,
            execute_pn,
            width=width,
        )
        return app
