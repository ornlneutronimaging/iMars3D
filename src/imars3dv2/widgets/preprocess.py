#!/usr/bin/env python3

import param
import panel as pn
import holoviews as hv
import numpy as np
from holoviews import opts
from holoviews.operation.datashader import rasterize
from imars3dv2.filters.gamma_filter import gamma_filter
from imars3dv2.filters.normalization import normalization


class Preprocess(param.Parameterized):
    # container to store images
    ct = param.Array(
        doc="radiograph stack as numpy array",
        precedence=-1,  # hide
    )
    ob = param.Array(
        doc="open beam stack as numpy array",
        precedence=-1,  # hide
    )
    df = param.Array(
        doc="dark field stack as numpy array",
        precedence=-1,  # hide
    )
    # actions
    filter_gamma_status = param.Boolean(default=False, doc="CT is gamma filtered")
    filter_gamma_action = param.Action(lambda x: x.param.trigger("filter_gamma_action"), label="GammaFilter")
    normalize_status = param.Boolean(default=False, doc="CT is normalized")
    normalize_action = param.Action(lambda x: x.param.trigger("normalize_action"), label="Normalize")
    # index for viewing
    idx_active_ct = param.Integer(default=0, doc="index of active ct")
    idx_active_ob = param.Integer(default=0, doc="index of active ob")
    idx_active_df = param.Integer(default=0, doc="index of active df")
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

    @param.depends("filter_gamma_action", watch=True)
    def gamma_filter(self):
        """use default input arg for now"""
        dtype = self.ct.dtype
        self.ct = gamma_filter(self.ct).astype(dtype)
        #
        self.filter_gamma_status = True
        pn.state.notifications.success("Gamma filter complete.", duration=0)

    @param.depends("normalize_action", watch=True)
    def normalize_radiograph(self):
        self.ct = normalization(
            self.ct,
            self.ob,
            self.df,
        )
        self.normalize_status = True
        pn.state.notifications.success("Normalization complete.", duration=0)

    @param.depends("ct", "idx_active_ct", "colormap", "colormap_scale")
    def ct_viewer(self):
        if self.ct is None:
            return pn.pane.Markdown("no CT to display")
        else:
            ct_active = self.ct[self.idx_active_ct]
            #
            img = rasterize(hv.Image(ct_active, bounds=(0, 0, ct_active.shape[1], ct_active.shape[0])))
            return img.opts(
                opts.Image(
                    width=400,
                    height=400,
                    tools=["hover"],
                    cmap=self.colormap,
                    cnorm=self.colormap_scale,
                ),
            ).hist()

    @param.depends("ob", "idx_active_ob", "colormap", "colormap_scale")
    def ob_viewer(self):
        if self.ob is None:
            return pn.pane.Markdown("no OB to display")
        else:
            ob_active = self.ob[self.idx_active_ob]
            #
            img = rasterize(hv.Image(ob_active, bounds=(0, 0, ob_active.shape[1], ob_active.shape[0])))
            return img.opts(
                opts.Image(
                    width=400,
                    height=400,
                    tools=["hover"],
                    cmap=self.colormap,
                    cnorm=self.colormap_scale,
                ),
            ).hist()

    @param.depends("df", "idx_active_df", "colormap", "colormap_scale")
    def df_viewer(self):
        if self.df is None:
            return pn.pane.Markdown("no DF to display")
        else:
            df_active = self.df[self.idx_active_df]
            #
            img = rasterize(hv.Image(df_active, bounds=(0, 0, df_active.shape[1], df_active.shape[0])))
            return img.opts(
                opts.Image(
                    width=400,
                    height=400,
                    tools=["hover"],
                    cmap=self.colormap,
                    cnorm=self.colormap_scale,
                ),
            ).hist()

    @param.output(param.Array)
    def get_data(self):
        return self.ct

    def panel(self):
        # gamma filter
        gf_pn = pn.Row(
            pn.widgets.BooleanStatus.from_param(
                self.param.filter_gamma_status,
                color="success",
                width=10,
                height=10,
            ),
            pn.widgets.Button.from_param(
                self.param.filter_gamma_action,
                width=80,
            ),
            height=50,
            width=150,
        )
        # normalize
        nz_pn = pn.Row(
            pn.widgets.BooleanStatus.from_param(
                self.param.normalize_status,
                color="success",
                width=10,
                height=10,
            ),
            pn.widgets.Button.from_param(
                self.param.normalize_action,
                width=80,
            ),
        )
        # control panel
        control_pn = pn.Card(
            gf_pn,
            nz_pn,
            width=200,
            header="**Control Panel**",
            collapsible=True,
        )
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
        #
        ct_control = pn.widgets.IntSlider.from_param(
            self.param.idx_active_ct,
            start=0,
            end=self.ct.shape[0],
            name="CT num",
        )
        ct_tab = pn.Column(self.ct_viewer, ct_control)
        #
        ob_control = pn.widgets.IntSlider.from_param(
            self.param.idx_active_ob,
            start=0,
            end=self.ob.shape[0],
            name="OB num",
        )
        ob_tab = pn.Column(self.ob_viewer, ob_control)
        #
        df_control = pn.widgets.IntSlider.from_param(
            self.param.idx_active_df,
            start=0,
            end=self.df.shape[0],
            name="DF num",
        )
        df_tab = pn.Column(self.df_viewer, df_control)
        viewer = pn.Tabs(
            ("CT", ct_tab),
            ("OB", ob_tab),
            ("DF", df_tab),
            sizing_mode="stretch_width",
        )
        #
        app = pn.Row(
            pn.Column(control_pn, cmap_pn),
            viewer,
        )
        return app
