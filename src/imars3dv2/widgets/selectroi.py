#!/usr/env/bin python3
import param
import panel as pn
import holoviews as hv
import numpy as np
import datetime
import os
import dxchange
from holoviews import opts
from holoviews import streams
from pathlib import Path
from imars3dv2.filters.crop import crop


class SelectROI(param.Parameterized):
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
    confirm_ROI_action = param.Action(lambda x: x.param.trigger("confirm_ROI_action"), label="Confirm ROI")
    crop2ROI_action = param.Action(lambda x: x.param.trigger("crop2ROI_action"), label="Crop to ROI")
    ct_checkpoint_action = param.Action(lambda x: x.param.trigger("ct_checkpoint_action"), label="Checkpoint")
    #
    top = param.Integer(doc="top of ROI")
    bottom = param.Integer(doc="bottom of ROI")
    left = param.Integer(doc="left of ROI")
    right = param.Integer(doc="right of ROI")

    # ROI selection
    roi_box = hv.Polygons([])
    roi_box_stream = streams.BoxEdit()

    @param.output(
        ("ct", param.Array),
        ("omegas", param.Array),
        ("recn_root", param.Path),
        ("temp_root", param.Path),
        ("recn_name", param.String),
    )
    def output(self):
        return (
            self.ct,
            self.omegas,
            self.recn_root,
            self.temp_root,
            self.recn_name,
        )

    @param.depends("ct_checkpoint_action", watch=True)
    def save_checkpoint(self):
        if self.ct is None:
            pn.state.warning("No CT to save")
        else:
            # make dir
            chk_root = datetime.datetime.now().isoformat().replace(":", "_")
            savedirname = f"{self.temp_root}/{self.recn_name}/{chk_root}"
            os.makedirs(savedirname)
            # save the current CT
            dxchange.writer.write_tiff_stack(
                data=self.ct,
                fname=f"{savedirname}/chk.tiff",
                axis=0,
                digit=5,
            )
            # save omega list as well
            np.save(
                file=f"{savedirname}/omegas.py",
                arr=self.omegas,
            )

    @param.depends("confirm_ROI_action", watch=True)
    def update_ROI(self):
        data = self.roi_box_stream.data
        self.top = int(data["y1"][0])
        self.bottom = int(data["y0"][0])
        self.left = int(data["x0"][0])
        self.right = int(data["x1"][0])

    def roi_control_pn(self, width=80):
        top = pn.widgets.IntInput.from_param(self.param.top, name="", disabled=True, width=width // 3)
        bottom = pn.widgets.IntInput.from_param(self.param.bottom, name="", disabled=True, width=width // 3)
        left = pn.widgets.IntInput.from_param(
            self.param.left,
            name="",
            disabled=True,
            width=width // 3,
        )
        right = pn.widgets.IntInput.from_param(
            self.param.right,
            name="",
            disabled=True,
            width=width // 3,
        )
        #
        confirm_ROI_button = pn.widgets.Button.from_param(
            self.param.confirm_ROI_action,
        )
        crop2ROI_button = pn.widgets.Button.from_param(
            self.param.crop2ROI_action,
        )
        return pn.Card(
            confirm_ROI_button,
            pn.Row(pn.Spacer(width=width // 6), top),
            pn.Row(left, right),
            pn.Row(pn.Spacer(width=width // 6), bottom),
            crop2ROI_button,
            width=width,
            header="Crop",
            collapsible=True,
        )

    @param.depends("crop2ROI_action", watch=True)
    def crop_to_RIO(self):
        crop_limit = (self.left, self.right, self.top, self.bottom)
        #
        if self.ct is None:
            pn.state.warning("No CT to crop")
        else:
            self.ct = crop(
                self.ct,
                crop_limit=crop_limit,
            )
        #
        if self.ob is None:
            pn.state.warning("No OB to crop")
        else:
            self.ob = crop(
                self.ob,
                crop_limit=crop_limit,
            )
        #
        if self.dc is None:
            pn.state.warning("No DC to crop")
        else:
            self.dc = crop(
                self.dc,
                crop_limit=crop_limit,
            )

    def cross_hair_view(self, x, y):
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
        if self.ct is None:
            return pn.pane.Markdown("no CT to display")
        # ct image object
        img = self._ct_active_view()
        # cross-hair pointer
        crosshair = streams.PointerXY(x=0, y=0, source=img)
        crosshair_dmap = hv.DynamicMap(self.cross_hair_view, streams=[crosshair])
        # sinogram view as dynamic map
        sino_dmap = hv.DynamicMap(self._sino_view, streams=[crosshair])
        # box select
        self.roi_box_stream = streams.BoxEdit(source=self.roi_box, num_objects=1)
        #
        viewer = (
            (img.hist() * crosshair_dmap * self.roi_box + sino_dmap)
            .cols(1)
            .opts(
                opts.Polygons(
                    fill_alpha=0.2,
                    line_color="red",
                )
            )
        )
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
        if self.ob is None:
            return pn.pane.Markdown("no OB to display")
        # no need for fancy viewer tools for OB
        img = self._ob_active_view()
        viewer = img.hist()
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
        if self.dc is None:
            return pn.pane.Markdown("no DC to display")
        #
        img = self._dc_active_view()
        viewer = img.hist()
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
        side_pn = pn.Column(
            self.plot_control(width=self.frame_width // 3),
            self.roi_control_pn(width=self.frame_width // 3),
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
