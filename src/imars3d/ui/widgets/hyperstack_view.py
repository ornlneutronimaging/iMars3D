#!/usr/bin/env python3
"""Hyperstack viewer for iMars3D.

To test the hyperstack viewer widget in a Jupyter notebook:

import panel as pn
from imars3d.ui.widgets.hyperstack_view import HyperstackView

pn.extension()
hv.extension("bokeh")

viewer = HyperstackView(data=skimage.data.brain())

now you can use either

- viewer or pn.Row(viewer) or viewer.servable() to check the widget in cell
- viewer.show() to check the widget in a separate window (on a bokeh server)
"""
import logging
import numpy as np
import panel as pn
import param
import holoviews as hv
from holoviews import opts
from holoviews import streams
from imars3d.ui.widgets.viewer2d import Viewer2D

logger = logging.getLogger(__name__)


class HyperstackView(Viewer2D):
    """Hyperstack viewer widget."""

    width = param.Integer(default=300, bounds=(0, None))
    height = param.Integer(default=300, bounds=(0, None))

    def __init__(self, **params):
        super().__init__(**params)

        self._panel = pn.Row(
            pn.Column(
                self.view_control_panel,
                self.view_region_control,
            ),
            self.viewer,
        )

        self.data = params.get("data", None)

    def view_region_control(self):
        """Return view region size control."""
        width_slider = pn.widgets.IntInput.from_param(
            self.param.width,
        )
        height_slider = pn.widgets.IntInput.from_param(
            self.param.height,
        )
        return pn.Column(
            width_slider,
            height_slider,
        )

    def cross_hair_view(self, x, y):
        """Return cross hair view."""
        return (hv.HLine(y) * hv.VLine(x)).opts(
            opts.HLine(
                color="yellow",
                line_width=0.5,
            ),
            opts.VLine(
                color="yellow",
                line_width=0.5,
            ),
        )

    def bottom_view(self, x: int, y: int):
        """Return bottom view."""
        if self.data is None:
            return pn.panel("no data")
        #
        img = self.data[:, int(y), :]
        return (
            hv.Image(
                (
                    np.arange(img.shape[1]),
                    np.arange(img.shape[0]),
                    img,
                ),
                kdims=["x", "y"],
                vdims=["intensity"],
            )
            * hv.VLine(x)
            * hv.HLine(self.idx_data)
        ).opts(
            opts.Image(
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                width=self.width,
                # data_aspect=1.0,
            ),
            opts.VLine(
                color="red",
                line_width=0.5,
            ),
            opts.HLine(
                color="red",
                line_width=0.5,
            ),
        )

    def side_view(self, x, y):
        """Return the side view."""
        if self.data is None:
            return pn.panel("no data")
        #
        img = self.data[:, :, int(x)]
        return (
            hv.Image(
                (
                    np.arange(img.shape[0]),
                    np.arange(img.shape[1]),
                    img.T,
                ),
                kdims=["y", "z"],
                vdims=["intensity"],
            )
            * hv.VLine(self.idx_data)
            * hv.HLine(y)
        ).opts(
            opts.Image(
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                height=self.height,
            ),
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
        "data",
        "idx_data",
        "colormap",
        "colormap_scale",
        "width",
        "height",
    )
    def viewer(self):
        """Image viewer."""
        # check 0
        if self.data is None:
            return pn.panel("No data to view.")
        # check 1
        if self.data.ndim != 3:
            return pn.panel("Data must be 3D.")
        # build the view
        img = self.data[self.idx_data, :, :]
        main = hv.Image(
            (
                np.arange(img.shape[1]),
                np.arange(img.shape[0]),
                img,
            ),
            kdims=["x", "z"],
            vdims=["intensity"],
        ).opts(
            opts.Image(
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                width=self.width,
                height=self.height,
            ),
        )
        crosshair = streams.PointerXY(x=0, y=0, source=main)
        crosshair_dmap = hv.DynamicMap(self.cross_hair_view, streams=[crosshair])
        main_view = main * crosshair_dmap
        bottom_view = hv.DynamicMap(self.bottom_view, streams=[crosshair])
        side_view = hv.DynamicMap(self.side_view, streams=[crosshair])
        return ((main_view + side_view) + bottom_view).cols(2)


if __name__ == "__main__":
    import skimage
    import panel as pn
    import holoviews as hv
    from imars3d.ui.widgets.hyperstack_view import HyperstackView

    pn.extension()
    hv.extension("bokeh")

    viewer = HyperstackView(data=skimage.data.brain())
