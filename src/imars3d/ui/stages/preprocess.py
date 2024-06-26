#!/usr/bin/env python3
"""Preprocessing stage for iMars3D."""
import param
import panel as pn
import holoviews as hv
import numpy as np
from holoviews import streams
from holoviews import opts
from holoviews.operation.datashader import rasterize
from pathlib import Path
from imars3d.backend.dataio.data import save_checkpoint as imars_save_checkpoint
from imars3d.ui.widgets.gamma_filter import GammaFilter
from imars3d.ui.widgets.normalization import Normalization
from imars3d.ui.widgets.denoise import Denoise
from imars3d.ui.widgets.ifc import IntensityFluctuationCorrection
from imars3d.ui.widgets.tilt import TiltCorrection
from imars3d.ui.widgets.ring_removal import RemoveRingArtifact


class Preprocess(param.Parameterized):
    """Preprocessing stage for iMars3D."""

    # -- Input data from previous step
    # data container
    ct = param.Array(
        doc="radiograph stack as numpy array",
        precedence=-1,  # hide
    )
    ob = param.Array(
        doc="open beam stack as numpy array",
        precedence=-1,  # hide
    )
    dc = param.Array(
        doc="dark current stack as numpy array",
        precedence=-1,  # hide
    )
    omegas = param.Array(
        doc="rotation angles in degress derived from tiff filename.",
    )
    recn_root = param.Path(
        default=Path.home(),
        doc="reconstruction results root, default should be proj_root/processed_data",
    )
    temp_root = param.Path(
        default=Path.home() / Path("tmp"),
        doc="intermedia results save location",
    )
    recn_name = param.String(
        default="myrecon",
        doc="reconstruction results folder name",
    )
    # index for viewing
    idx_active_ct = param.Integer(default=0, doc="index of active ct")
    idx_active_ob = param.Integer(default=0, doc="index of active ob")
    idx_active_dc = param.Integer(default=0, doc="index of active dc")
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
    frame_width = param.Integer(default=500, doc="viewer frame size")
    #
    ct_checkpoint_action = param.Action(lambda x: x.param.trigger("ct_checkpoint_action"), label="Checkpoint")
    # filters
    gamma_filter = GammaFilter()
    norm_filter = Normalization()
    denoise_filter = Denoise()
    ifc_filter = IntensityFluctuationCorrection()
    tilt_correction_filter = TiltCorrection()
    remove_ring_filter = RemoveRingArtifact()

    @param.output(
        ("ct", param.Array),
        ("omegas", param.Array),
        ("recn_root", param.Path),
        ("temp_root", param.Path),
        ("recn_name", param.String),
    )
    def output(self):
        """Output data for next step."""
        return (
            self.ct,
            self.omegas,
            self.recn_root,
            self.temp_root,
            self.recn_name,
        )

    @param.depends("ct_checkpoint_action", watch=True)
    def save_checkpoint(self):
        """Save current state to checkpoint."""
        if self.ct is None:
            pn.state.warning("No CT to save")
        else:
            imars_save_checkpoint(data=self.ct, outputbase=self.temp_root, name=self.recn_name, omegas=self.omegas)

    def cross_hair_view(self, x, y):
        """Cross hair view."""
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

    def _sino_view(self, x, y):
        #
        sino = hv.Image(
            (
                np.arange(self.ct.shape[2]),
                np.arange(self.ct.shape[0]),
                self.ct[:, int(y), :],
            ),
            kdims=["x", "ω"],
            vdims=["count"],
        )
        return (sino * hv.VLine(x) * hv.HLine(self.idx_active_ct)).opts(
            opts.Image(
                frame_width=self.frame_width,
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                invert_yaxis=True,
                xaxis=None,
                yaxis=None,
                title="sinogram",
            ),
            opts.VLine(
                color="yellow",
                line_width=0.5,
            ),
            opts.HLine(
                color="yellow",
                line_width=0.5,
            ),
        )

    def _ct_active_view(self):
        ct_active = self.ct[self.idx_active_ct]
        return hv.Image(
            (
                np.arange(ct_active.shape[1]),
                np.arange(ct_active.shape[0]),
                ct_active,
            ),
            kdims=["x", "y"],
            vdims=["count"],
        ).opts(
            opts.Image(
                frame_width=self.frame_width,
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                data_aspect=1.0,
                invert_yaxis=True,
                xaxis=None,
                yaxis=None,
            )
        )

    def _ob_active_view(self):
        ob_active = self.ob[self.idx_active_ob]
        return hv.Image(
            (
                np.arange(ob_active.shape[1]),
                np.arange(ob_active.shape[0]),
                ob_active,
            ),
            kdims=["x", "y"],
            vdims=["count"],
        ).opts(
            opts.Image(
                frame_width=self.frame_width,
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                data_aspect=1.0,
                invert_yaxis=True,
                xaxis=None,
                yaxis=None,
            )
        )

    def _dc_active_view(self):
        dc_active = self.dc[self.idx_active_dc]
        return hv.Image(
            (
                np.arange(dc_active.shape[1]),
                np.arange(dc_active.shape[0]),
                dc_active,
            ),
            kdims=["x", "y"],
            vdims=["count"],
        ).opts(
            opts.Image(
                frame_width=self.frame_width,
                tools=["hover"],
                cmap=self.colormap,
                cnorm=self.colormap_scale,
                data_aspect=1.0,
                invert_yaxis=True,
                xaxis=None,
                yaxis=None,
            )
        )

    @param.depends(
        "frame_width",
        "idx_active_ct",
        "colormap",
        "colormap_scale",
    )
    def ct_viewer(self):
        """Radiograph (CT) viewer."""
        if self.ct is None:
            return pn.pane.Markdown("no CT to display")
        # ct image object
        img = self._ct_active_view()
        # cross-hair pointer
        crosshair = streams.PointerXY(x=0, y=0, source=img)
        crosshair_dmap = hv.DynamicMap(self.cross_hair_view, streams=[crosshair])
        # sinogram view as dynamic map
        sino_dmap = hv.DynamicMap(self._sino_view, streams=[crosshair])
        #
        viewer = rasterize(img.hist() * crosshair_dmap + sino_dmap).cols(1)
        #
        save_ct_button = pn.widgets.Button.from_param(
            self.param.ct_checkpoint_action,
            name="Save CT",
            width=self.frame_width // 4,
            align="center",
        )
        ct_num_control = pn.widgets.IntSlider.from_param(
            self.param.idx_active_ct,
            start=0,
            end=self.ct.shape[0],
            name="CT num",
            width=self.frame_width // 2,
        )
        ct_control = pn.Row(save_ct_button, ct_num_control)
        return pn.Column(ct_control, viewer)

    @param.depends(
        "frame_width",
        "idx_active_ob",
        "colormap",
        "colormap_scale",
    )
    def ob_viewer(self):
        """Open beam viewer."""
        if self.ob is None:
            return pn.pane.Markdown("no OB to display")
        # no need for fancy viewer tools for OB
        img = self._ob_active_view()
        viewer = rasterize(img.hist())
        #
        ob_control = pn.widgets.IntSlider.from_param(
            self.param.idx_active_ob,
            start=0,
            end=self.ob.shape[0],
            name="OB num",
            width=self.frame_width // 2,
        )
        return pn.Column(ob_control, viewer)

    @param.depends(
        "frame_width",
        "idx_active_dc",
        "colormap",
        "colormap_scale",
    )
    def dc_viewer(self):
        """Dark current viewer."""
        if self.dc is None:
            return pn.pane.Markdown("no DC to display")
        #
        img = self._dc_active_view()
        viewer = rasterize(img.hist())
        #
        dc_control = pn.widgets.IntSlider.from_param(
            self.param.idx_active_dc,
            start=0,
            end=self.dc.shape[0],
            name="DC num",
            width=self.frame_width // 2,
        )
        return pn.Column(dc_control, viewer)

    def plot_control(self, width=80):
        """Plot control panel."""
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
        """Panel view."""
        # side panel width
        width = self.frame_width // 2
        # filters panel
        self.gamma_filter.parent = self
        self.norm_filter.parent = self
        self.denoise_filter.parent = self
        self.ifc_filter.parent = self
        self.tilt_correction_filter.parent = self
        self.remove_ring_filter.parent = self
        filters_pn = pn.Accordion(
            ("Gamma", self.gamma_filter.panel(width=width)),
            ("Normalization", self.norm_filter.panel(width=width)),
            ("Denoise", self.denoise_filter.panel(width=width)),
            ("IFC", self.ifc_filter.panel(width=width)),
            ("Tilt correction", self.tilt_correction_filter.panel(width=width)),
            ("Ring removal", self.remove_ring_filter.panel(width=width)),
            width=int(width * 1.1),  # expand a little bit due to using Accordion
        )
        #
        side_pn = pn.Column(
            self.plot_control(width=int(width * 1.1)),
            filters_pn,
        )
        #
        view_pn = pn.Tabs(
            ("CT", self.ct_viewer),
            ("OB", self.ob_viewer),
            ("DC", self.dc_viewer),
        )
        #
        app = pn.Row(side_pn, view_pn)
        return app
