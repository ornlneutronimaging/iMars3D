#!/usr/bin/env python3

import numpy as np
import param
import panel as pn
import holoviews as hv
from holoviews import opts
from holoviews import streams


class Visualization(param.Parameterized):
    recon = param.Array(
        doc="reconstruction results as numpy array",
        precedence=-1,  # hide
    )
    idx_y = param.Integer(default=0, bounds=(0, None), doc="index of the y axis for recon stack")
    # cmap
    colormap = param.Selector(
        default="gray",
        objects=["gray", "viridis", "plasma"],
        doc="colormap used for images",
    )
    colormap_scale = param.Selector(
        default="linear",
        objects=["linear", "log", "eq_hist"],
        doc="colormap scale for displaying images",
    )
    # image size
    frame_width = param.Integer(default=500, doc="viewer frame size")

    def cross_hair_view(self, x, y):
        return (hv.HLine(y) * hv.VLine(x)).opts(
            opts.HLine(
                color="red",
                line_width=0.5,
            ),
            opts.VLine(
                color="red",
                line_width=0.5,
            ),
        )

    def xz_view(self):
        # main, top down
        xzview = self.recon[self.idx_y, :, :]
        return hv.Image(
            (
                np.arange(xzview.shape[1]),
                np.arange(xzview.shape[0]),
                xzview,
            ),
            kdims=["x", "z"],
            vdims=["intensity"],
        ).opts(
            opts.Image(
                frame_width=self.frame_width,
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                data_aspect=1.0,
            )
        )

    def xy_view(self, x, y):
        z = int(y)
        # bottom
        xyview = self.recon[:, int(z), :]
        img = hv.Image(
            (
                np.arange(xyview.shape[1]),
                np.arange(xyview.shape[0]),
                xyview,
            ),
            kdims=["x", "y"],
            vdims=["intensity"],
        ).opts(
            opts.Image(
                frame_width=self.frame_width,
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                data_aspect=1.0,
            )
        )
        return (img * hv.VLine(x) * hv.HLine(self.idx_y)).opts(
            opts.VLine(
                color="red",
                line_width=0.5,
            ),
            opts.HLine(
                color="red",
                line_width=0.5,
            ),
        )

    def yz_view(self, x, y):
        z = int(y)
        # side
        yzview = self.recon[:, :, int(x)]
        # frame width
        frame_width = int(self.frame_width * self.recon.shape[0] / self.recon.shape[1])
        img = hv.Image(
            (
                np.arange(yzview.shape[0]),
                np.arange(yzview.shape[1]),
                yzview.T,
            ),
            kdims=["y", "z"],
            vdims=["intensity"],
        ).opts(
            opts.Image(
                frame_width=frame_width,
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                data_aspect=1.0,
            )
        )
        return (img * hv.VLine(self.idx_y) * hv.HLine(z)).opts(
            opts.VLine(
                color="red",
                line_width=0.5,
            ),
            opts.HLine(
                color="red",
                line_width=0.5,
            ),
        )

    @param.depends(
        "frame_width",
        "idx_y",
        "colormap",
        "colormap_scale",
    )
    def recon_orthorgonal_view(self):
        if self.recon is None:
            return pn.pane.Markdown("no reconstruction to show")
        # control
        y_slider = pn.widgets.IntSlider.from_param(
            self.param.idx_y,
            name="y",
            start=0,
            end=self.recon.shape[0] - 1,
            step=1,
        )
        # -- main view
        main = self.xz_view()
        crosshair = streams.PointerXY(x=0, y=0, source=main)
        crosshair_dmap = hv.DynamicMap(self.cross_hair_view, streams=[crosshair])
        main_view = main * crosshair_dmap
        # -- side view
        side_view = hv.DynamicMap(self.yz_view, streams=[crosshair])
        # -- bottom view
        bottom_view = hv.DynamicMap(self.xy_view, streams=[crosshair])
        # -- composite viewer
        viewer = (main_view.hist() + side_view + bottom_view).cols(2)
        return pn.Column(y_slider, viewer)

    def plot_control(self, width=80):
        # color map
        cmap = pn.widgets.Select.from_param(
            self.param.colormap,
            name="colormap",
        )
        cmapscale = pn.widgets.Select.from_param(
            self.param.colormap_scale,
            name="colormap scale",
        )
        framewidth = pn.widgets.LiteralInput.from_param(
            self.param.frame_width,
            name="frame width",
        )
        plot_pn = pn.Card(
            cmap,
            cmapscale,
            framewidth,
            width=width,
            header="Diaply",
            collapsible=True,
        )
        return plot_pn

    def panel(self):
        width = self.frame_width // 2
        # side panel
        side_pn = pn.Column(
            self.plot_control(width=width),
            width=int(width * 1.1),
        )
        # main panel
        main_pn = self.recon_orthorgonal_view
        #
        app = pn.Row(side_pn, main_pn)
        return app
