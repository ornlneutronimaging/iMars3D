#!/usr/bin/env python3

import param
import panel as pn
import holoviews as hv
import numpy as np
import datetime
import os
import dxchange
from holoviews import streams
from holoviews import opts
from holoviews.operation.datashader import rasterize
from pathlib import Path
from imars3d.backend.reconstruction import recon
from imars3d.ui.widgets.rotation import FindRotationCenter


class Reconstruction(param.Parameterized):
    """
    Panel for conduction guided reconstruction with iMars3D.
    """

    # -- data container
    # ** input data from previous step
    ct = param.Array(
        doc="radiograph stack as numpy array",
        precedence=-1,  # hide
    )
    omegas = param.Array(
        doc="rotation angles in degress derived from tiff filename.",
    )
    recn_root = param.Path(
        default=Path.home(),
        doc="reconstruction results root, default should be proj_root/shared/processed_data",
    )
    temp_root = param.Path(
        default=Path.home() / Path("tmp"),
        doc="intermedia results save location",
    )
    recn_name = param.String(
        default="myrecon",
        doc="reconstruction results folder name",
    )
    # ** output reconstruction results
    recon = param.Array(
        doc="reconstruction results as numpy array",
        precedence=-1,  # hide
    )
    # reconstruction control
    algorithm = param.Selector(
        default="gridrec",
        objects=[
            "fbp",
            "gridrec",
            "art",
            "bart",
            "mlem",
            "osem",
            "ospml_hybrid",
            "ospml_quad",
            "pml_hybrid",
            "pml_quad",
            "sirt",
            "tv",
            "grad",
            "tikh",
        ],
        doc="algorithm provided by tomopy",
    )
    post_recon_filter = param.Selector(
        default="hann",
        objects=["none", "shepp", "cosine", "hann", "hamming", "ramlak", "parzen", "butterworth"],
        doc="post recon filter",
    )
    # -- viewer
    idx_active_ct = param.Integer(default=0, doc="index of active ct")
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
    # check point
    ct_checkpoint_action = param.Action(lambda x: x.param.trigger("ct_checkpoint_action"), label="Checkpoint")
    # rotation center
    rotation_center_finder = FindRotationCenter()
    #
    execute = param.Action(lambda x: x.param.trigger("execute"), label="Execute")
    status = param.Boolean(default=False, doc="Ring removal completion status")
    # save recon results
    recon_save = param.Action(lambda x: x.param.trigger("recon_save"), label="Checkpoint")

    @param.depends("execute", watch=True)
    def apply(self):
        # sanity check
        if self.ct is None:
            pn.state.warning("no CT found!")
            return
        if self.omegas is None:
            pn.state.warning("no omegas provided")
            return
        #
        self.recon = recon(
            arrays=self.ct,
            theta=np.radians(self.omegas),
            center=self.rotation_center_finder.rot_center,
            algorithm=self.algorithm,
            filter_name=self.post_recon_filter,
        )
        #
        self.status = True
        #
        pn.state.notifications.success("Reconstruction complete.", duration=3000)

    @param.output(
        ("recon", param.Array),
    )
    def output(self):
        return self.recon

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

    @param.depends("recon_save", watch=True)
    def save_reconstruction_results(self):
        if self.recon is None:
            pn.state.warning("No reconstruction results to save")
        else:
            # make dir
            chk_root = datetime.datetime.now().isoformat().replace(":", "_")
            savedirname = f"{self.recn_root}/{self.recn_name}/{chk_root}"
            os.makedirs(savedirname)
            # save the current CT
            dxchange.writer.write_tiff_stack(
                data=self.recon,
                fname=f"{savedirname}/recon.tiff",
                axis=0,
                digit=5,
            )
            # save omega list as well
            np.save(
                file=f"{savedirname}/omegas.py",
                arr=self.omegas,
            )
            # save the rotation center
            with open(f"{savedirname}/rot_center.txt", "w") as f_rotcnt:
                f_rotcnt.write(f"{self.rotation_center_finder.rot_center}")

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
        "recon",
        "colormap",
        "colormap_scale",
    )
    def recon_viewer(self):
        if self.recon is None:
            return pn.pane.Markdown("no recontruction results to display")
        #
        ds = hv.Dataset(
            (
                np.arange(self.recon.shape[2]),
                np.arange(self.recon.shape[1]),
                np.arange(self.recon.shape[0]),
                self.recon,
            ),
            ["x", "z", "y"],
            "intensity",
        )
        img = ds.to(hv.Image, ["x", "z"], dynamic=True).opts(
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
        #
        save_recon_button = pn.widgets.Button.from_param(
            self.param.recon_save,
            name="Save Reconstruction",
            width=self.frame_width // 4,
            align="center",
        )
        return pn.Column(save_recon_button, rasterize(img.hist()))

    def recon_panel(self, width=200):
        # methods
        algorithm_select = pn.widgets.Select.from_param(
            self.param.algorithm,
            name="Algorithm",
            width=int(width / 1.2),
        )
        filter_select = pn.widgets.Select.from_param(
            self.param.post_recon_filter,
            name="PostReconFilter",
            width=int(width / 1.2),
        )
        # action
        status_indicator = pn.widgets.BooleanStatus.from_param(
            self.param.status,
            color="success",
        )
        execute_button = pn.widgets.Button.from_param(
            self.param.execute,
            width=width // 2,
        )
        action_pn = pn.Row(status_indicator, execute_button, width=width)
        #
        recon_panel = pn.WidgetBox(
            "**Reconstruction control**",
            algorithm_select,
            filter_select,
            action_pn,
            width=width,
        )
        return recon_panel

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
        # rotation center finder
        self.rotation_center_finder.parent = self
        # -- side panel
        width = self.frame_width // 2
        rotcnt_pn = pn.WidgetBox(
            "Rotation Center",
            self.rotation_center_finder.panel(width=width),
        )
        side_pn = pn.Column(
            self.plot_control(width=width),
            rotcnt_pn,
            self.recon_panel(width=width),
            width=int(width * 1.1),
        )
        # -- viewer
        viewer = pn.Tabs(
            ("CT", self.ct_viewer),
            ("Recon", self.recon_viewer),
        )
        #
        app = pn.Row(side_pn, viewer)
        return app
