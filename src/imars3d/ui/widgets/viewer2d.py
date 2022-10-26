#!/usr/bin/env python3
"""2D Image viewer for iMars3D.

To test the 2D viewer widget in a Jupyter notebook:

import skimage
import panel as pn
import holoview as hv
from imars3d.ui.widgets.viewer2d import Viewer2D

pn.extension()
hv.extension("bokeh")

viewer = Viewer2D(data=skimage.data.brain())

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

logger = logging.getLogger(__name__)


class Viewer2D(pn.viewable.Viewer):
    """2D viewer class to view stack of images."""

    data = param.Array(doc="Image stack for viewing")
    idx_data = param.Integer(
        default=0,
        bounds=(0, None),
        doc="data stack images.",
    )
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

    def __init__(self, data, **params):
        super().__init__(**params)

        self._panel = pn.Row(
            self.view_control_panel,
            self.viewer,
            sizing_mode="stretch_width",
        )

        self.data = data

    @param.depends("data")
    def view_control_panel(self):
        """View control widgest."""
        if self.data is None:
            idx_pn = pn.panel("no data to select")
        else:
            if self.data.ndim == 2:
                idx_pn = pn.panel("2D image")
            elif self.data.ndim == 3:
                idx_pn = pn.widgets.IntSlider.from_param(
                    self.param.idx_data,
                    name="index",
                    start=0,
                    end=self.data.shape[0],
                    value_throttled=True,
                )
            else:
                logger.error(f"Unsupported data dimension: {self.data.ndim}.")

        cmap_pn = pn.widgets.Select.from_param(
            self.param.colormap,
            name="ColorMap",
        )

        cscale_pn = pn.widgets.Select.from_param(
            self.param.colormap_scale,
            name="Scale",
        )

        return pn.Column(
            idx_pn,
            cmap_pn,
            cscale_pn,
        )

    @param.depends(
        "data",
        "idx_data",
        "colormap",
        "colormap_scale",
    )
    def viewer(self):
        """Image viewer."""
        # check 0
        if self.data is None:
            return pn.panel("No data to view.")
        # check 1
        if self.data.ndim == 2:
            img = self.data
        elif self.data.ndim == 3:
            img = self.data[self.idx_data]
        else:
            logger.error(f"Cannot display data of given diemsion: {self.data.ndim}")
        #
        return (
            hv.Image(
                (
                    np.arange(img.shape[1]),
                    np.arange(img.shape[0]),
                    img,
                ),
                kdims=["x", "y"],
                vdims=["count"],
            )
            .hist()
            .opts(
                opts.Image(
                    tools=["hover"],
                    cmap=self.colormap,
                    cnorm=self.colormap_scale,
                    data_aspect=1.0,
                    invert_yaxis=True,
                    xaxis=None,
                    yaxis=None,
                )
            )
        )

    def __panel__(self):
        return self._panel


if __name__ == "__main__":
    import skimage

    pn.extension()
    hv.extension("bokeh")

    viewer = Viewer2D(data=skimage.data.brain())
