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

    @param.depends("filter_gamma_action", watch=True)
    def gamma_filter(self):
        """use default input arg for now"""
        dtype = self.ct.dtype
        self.ct = gamma_filter(self.ct).astype(dtype)
        #
        self.filter_gamma_status = True
        pn.state.notifications.success("Gamma filter complete.", duration=3000)

    @param.depends("normalize_action", watch=True)
    def normalize_radiograph(self):
        self.ct = normalization(
            self.ct,
            self.ob,
            self.df,
        )
        self.normalize_status = True
        pn.state.notifications.success("Normalization complete.", duration=3000)

    @param.depends("ct")
    def ct_viewer(self):
        if self.ct is None:
            return pn.pane.Markdown("no CT to display")
        else:
            ds = hv.Dataset(
                (
                    np.arange(0, self.ct.shape[2]),
                    np.arange(0, self.ct.shape[1]),
                    np.arange(0, self.ct.shape[0]),
                    self.ct,
                ),
                ["x", "y", "n"],
                "count",
            )
            #
            viewer = (
                rasterize(
                    ds.to(hv.Image, ["x", "y"], dynamic=True),
                )
                .opts(
                    opts.Image(
                        tools=["hover"],
                        cmap="gray",
                        invert_yaxis=True,
                    )
                )
                .hist()
            )
            return viewer

    @param.depends("ob")
    def ob_viewer(self):
        if self.ob is None:
            return pn.pane.Markdown("no OB to display")
        else:
            ds = hv.Dataset(
                (
                    np.arange(0, self.ob.shape[2]),
                    np.arange(0, self.ob.shape[1]),
                    np.arange(0, self.ob.shape[0]),
                    self.ob,
                ),
                ["x", "y", "n"],
                "count",
            )
            viewer = (
                rasterize(
                    ds.to(hv.Image, ["x", "y"], dynamic=True),
                )
                .opts(
                    opts.Image(
                        tools=["hover"],
                        cmap="gray",
                        invert_yaxis=True,
                    )
                )
                .hist()
            )
            return viewer

    @param.depends("df")
    def df_viewer(self):
        if self.df is None:
            return pn.pane.Markdown("no DF to display")
        else:
            ds = hv.Dataset(
                (
                    np.arange(0, self.df.shape[2]),
                    np.arange(0, self.df.shape[1]),
                    np.arange(0, self.df.shape[0]),
                    self.df,
                ),
                ["x", "y", "n"],
                "count",
            )
            viewer = (
                rasterize(
                    ds.to(hv.Image, ["x", "y"], dynamic=True),
                )
                .opts(
                    opts.Image(
                        tools=["hover"],
                        cmap="gray",
                        invert_yaxis=True,
                    )
                )
                .hist()
            )
            return viewer

    @param.output(param.Array)
    def get_data(self):
        return self.ct

    def panel(self):
        # gamma filter
        gf_pn = pn.Param(
            self,
            name="",
            parameters=["filter_gamma_status", "filter_gamma_action"],
            widgets={
                "filter_gamma_status": {
                    "widget_type": pn.widgets.BooleanStatus,
                    "color": "success",
                    "width": 10,
                    "height": 10,
                },
                "filter_gamma_action": {
                    "width": 80,
                },
            },
            default_layout=pn.Row,
            height=30,
            width=150,
        )
        # normalize
        nz_pn = pn.Param(
            self,
            name="",
            parameters=["normalize_status", "normalize_action"],
            widgets={
                "normalize_status": {
                    "widget_type": pn.widgets.BooleanStatus,
                    "color": "success",
                    "width": 10,
                    "height": 10,
                },
                "normalize_action": {
                    "width": 80,
                },
            },
            default_layout=pn.Row,
        )
        # control panel
        control_pn = pn.Card(
            gf_pn,
            nz_pn,
            width=200,
            header="**Control Panel**",
            collapsible=False,
        )
        #
        viewer = pn.Tabs(
            ("CT", self.ct_viewer),
            ("OB", self.ob_viewer),
            ("DF", self.df_viewer),
            sizing_mode="stretch_width",
        )
        #
        app = pn.Row(control_pn, viewer)
        return app
