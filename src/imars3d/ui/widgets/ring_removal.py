#!/usr/bin/env python3
"""Widgets for ring removal."""
import param
import panel as pn
from imars3d.backend.corrections.ring_removal import remove_ring_artifact


class RemoveRingArtifact(param.Parameterized):
    """Ring removal widget.

    widget of ring artifact removal filter from iMars3D, must have a parent
    widget with valid ct stack.
    """

    parent = param.Parameter()
    #
    kernel_size = param.Integer(
        default=5,
        bounds=(3, None),
        doc="kernel size of moving window during local smoothing",
    )
    sub_division = param.Integer(
        default=10,
        bounds=(2, None),
        doc="num of subsections for subdividing sinogram",
    )
    correction_range = param.Range(
        default=(0.9, 1.1), doc="Multiplicative correction factor is capped within given range."
    )
    #
    execute = param.Action(lambda x: x.param.trigger("execute"), label="Execute")
    status = param.Boolean(default=False, doc="Ring removal completion status")

    @param.depends("execute", watch=True)
    def apply(self):
        """Apply ring removal."""
        if self.parent.ct is None:
            pn.state.notifications.warning("no CT found", duration=3000)
        else:
            self.parent.ct = remove_ring_artifact(
                arrays=self.parent.ct,
                kernel_size=self.kernel_size,
                sub_division=self.sub_division,
                correction_range=self.correction_range,
            )
            #
            self.status = True
            #
            pn.state.notifications.success("Ring removal complete.", duration=3000)

    def panel(self, width=200):
        """App card view."""
        kernel_size_input = pn.widgets.IntInput.from_param(
            self.param.kernel_size,
            name="Kernel size",
        )
        sub_division_input = pn.widgets.IntInput.from_param(
            self.param.sub_division,
            name="Divide sinogram into",
        )
        correction_range_input = pn.widgets.EditableRangeSlider.from_param(
            self.param.correction_range,
            name="Correction factor",
            start=0.5,
            end=1.5,
            step=0.01,
            width=int(0.7 * width),
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
            kernel_size_input,
            sub_division_input,
            correction_range_input,
            pn.Row(status_indicator, execute_button, width=width),
            width=width,
        )
        return app
