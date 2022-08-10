#!/usr/env/bin python3
import param
import panel as pn
import holoviews as hv
import numpy as np
from holoviews import opts
from holoviews import streams
from holoviews.operation.datashader import rasterize
from imars3dv2.filters.crop import crop


class SelectROI(param.Parameterized):
    # container to store images
    ct = param.Array(
        doc="radiograph stack as numpy array",
        precedence=-1,  # hide
    )
    # index for viewing
    idx_active_ct = param.Integer(default=0, doc="index of active ct")
    idx_active_sino = param.Integer(default=0, doc="index of active sinogram")
    # cmap
    colormap = param.Selector(
        default="gray",
        objects=["gray", "viridis", "plasma"],
        doc="colormap used for images",
    )
    colormap_scale = param.Selector(
        default="linear",
        objects=["linear", "log"],
        doc="colormap scale for displaying images",
    )
    #
    guess_ROI_action = param.Action(lambda x: x.param.trigger("guess_ROI_action"), label="Auto ROI")
    confirm_ROI_action = param.Action(lambda x: x.param.trigger("confirm_ROI_action"), label="Confirm ROI")
    crop2ROI_action = param.Action(lambda x: x.param.trigger("crop2ROI_action"), label="Crop to ROI")
    # ROI selection
    polys = hv.Polygons([])
    boxstream = None
    sino_line = None
    #
    top = param.Integer(doc="top of ROI")
    bottom = param.Integer(doc="bottom of ROI")
    left = param.Integer(doc="left of ROI")
    right = param.Integer(doc="right of ROI")

    @param.output(
        ("ct", param.Array),
    )
    def get_data(self):
        return self.ct

    @param.depends("confirm_ROI_action", watch=True)
    def update_ROI(self):
        data = self.boxstream.data
        self.top = int(data["y1"][0])
        self.bottom = int(data["y0"][0])
        self.left = int(data["x0"][0])
        self.right = int(data["x1"][0])

    def display_roi(self, width=80):
        top = pn.widgets.IntInput.from_param(self.param.top, name="", disabled=True, width=width)
        bottom = pn.widgets.IntInput.from_param(self.param.bottom, name="", disabled=True, width=width)
        left = pn.widgets.IntInput.from_param(
            self.param.left,
            name="",
            disabled=True,
            width=width,
        )
        right = pn.widgets.IntInput.from_param(
            self.param.right,
            name="",
            disabled=True,
            width=width,
        )
        return pn.Column(
            pn.Row(pn.Spacer(width=width // 2), top),
            pn.Row(left, right),
            pn.Row(pn.Spacer(width=width // 2), bottom),
        )

    @param.depends("crop2ROI_action", watch=True)
    def crop_to_RIO(self):
        crop_limit = (self.left, self.right, self.top, self.bottom)
        self.ct = crop(
            self.ct,
            crop_limit=crop_limit,
        )

    @param.depends(
        "ct",
        "idx_active_ct",
        "idx_active_sino",
        "colormap",
        "colormap_scale",
    )
    def ct_viewer(self):
        if self.ct is None:
            return pn.pane.Markdown("no CT to display")
        else:
            # ct
            ct_active = self.ct[self.idx_active_ct]
            img = rasterize(hv.Image((np.arange(ct_active.shape[1]), np.arange(ct_active.shape[0]), ct_active)))
            # sino line
            self.sino_line = hv.HLine(self.idx_active_sino)
            return (
                (img * self.polys * self.sino_line)
                .opts(
                    opts.Image(
                        tools=["hover"],
                        cmap=self.colormap,
                        cnorm=self.colormap_scale,
                        data_aspect=1.0,
                        invert_yaxis=True,
                        title="radiograph",
                    ),
                    opts.Polygons(
                        fill_alpha=0.2,
                        line_color="red",
                    ),
                    opts.HLine(
                        color="red",
                        line_width=0.5,
                    ),
                )
                .hist()
            )

    @param.depends(
        "ct",
        "idx_active_ct",
        "idx_active_sino",
        "colormap",
        "colormap_scale",
    )
    def sino_viewer(self):
        # sino
        sino_active = self.ct[:, self.idx_active_sino, :]
        sino = rasterize(hv.Image((np.arange(sino_active.shape[1]), np.arange(sino_active.shape[0]), sino_active)))
        return sino.opts(
            opts.Image(
                width=500,
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                shared_axes=False,
                title="sinogram",
            ),
        ).hist()

    def panel(self):
        # color map
        cmap = pn.widgets.Select.from_param(
            self.param.colormap,
            name="colormap",
        )
        cmapscale = pn.widgets.Select.from_param(
            self.param.colormap_scale,
            name="colormap scale",
        )
        cmap_pn = pn.Card(
            cmap,
            cmapscale,
            width=200,
            header="Diaply",
            collapsible=True,
        )
        # crop control
        confirm_ROI_button = pn.widgets.Button.from_param(
            self.param.confirm_ROI_action,
        )
        crop2ROI_button = pn.widgets.Button.from_param(
            self.param.crop2ROI_action,
        )
        crop_control_pn = pn.Card(
            confirm_ROI_button,
            self.display_roi,
            crop2ROI_button,
            width=200,
            header="Crop",
            collapsible=True,
        )
        # intensity fluctuation control
        # CT&Sino view
        # -- init
        self.boxstream = streams.BoxEdit(source=self.polys, num_objects=1)
        # -- build view
        ct_control = pn.widgets.IntSlider.from_param(
            self.param.idx_active_ct,
            start=0,
            end=self.ct.shape[0],
            name="CT num",
        )
        ct_tab = pn.Column(self.ct_viewer, ct_control)
        # sino view
        sino_control = pn.widgets.IntInput.from_param(
            self.param.idx_active_sino,
            start=0,
            end=self.ct.shape[1],
            value=self.ct.shape[1] // 2,
            name="Sino(y) num",
            width=80,
        )
        sino_tab = pn.Row(self.sino_viewer, sino_control)
        # final app
        app = pn.Row(
            pn.Column(cmap_pn, crop_control_pn),
            ct_tab,
            sino_tab,
        )
        return app
