#!/usr/bin/env python3
"""Widgets for rotation."""
import param
import panel as pn
from imars3d.backend.diagnostics.rotation import find_rotation_center


class FindRotationCenter(param.Parameterized):
    """Rotation center finder widget.

    widget of rotation center finder filter from iMars3D, must have a parent
    widget with valid ct stack
    """

    parent = param.Parameter()
    #
    auto_atol = param.Boolean(default=True, doc="use auto atol during rotation center finding")
    atol = param.Number(
        default=0.2, bounds=(0, None), doc="tolerance for the search of 180 deg paris, default is 0.2 degrees"
    )
    rot_center = param.Number(bounds=(0, None), doc="rotation center")
    #
    execute = param.Action(lambda x: x.param.trigger("execute"), label="Execute")
    status = param.Boolean(default=False, doc="Ring removal completion status")

    @param.depends("execute", watch=True)
    def apply(self):
        """Apply rotation center finder."""
        if self.parent.ct is None:
            pn.state.notifications.warning("no CT found", duration=3000)
        else:
            # sanity check
            if self.parent.ct is None:
                pn.state.warning("no CT found!")
                return
            if self.parent.omegas is None:
                pn.state.warning("no omegas provided")
                return
            #
            self.rot_center = find_rotation_center(
                arrays=self.parent.ct,
                angles=self.parent.omegas,
                in_degrees=True,
                atol_deg=self.atol,
            )
            #
            self.status = True
            #
            pn.state.notifications.success("Rotation center found.", duration=3000)

    def panel(self, width=200):
        """App card view."""
        #
        auto_atol_status = pn.widgets.Checkbox.from_param(
            self.param.auto_atol,
            name="auto",
        )
        atol_input = pn.widgets.LiteralInput.from_param(
            self.param.atol,
            name="atol (deg)",
            value=360.0 / self.parent.ct.shape[0],
            width=int(width / 2.5),
            disabled=self.auto_atol,
        )
        atol_pn = pn.WidgetBox(
            "atol (deg)",
            auto_atol_status,
            atol_input,
            width=width // 2,
        )
        #
        rot_cnt_display = pn.widgets.LiteralInput.from_param(
            self.param.rot_center,
            name="Rotation center",
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
        app = pn.Column(
            atol_pn,
            pn.Row(status_indicator, execute_button, width=width),
            rot_cnt_display,
            width=width,
        )
        return app
