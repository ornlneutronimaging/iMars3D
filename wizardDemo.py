#!/usr/bin/env python3

import numpy as np
import tifffile
import param
import panel as pn
import holoviews as hv
from holoviews import opts
from holoviews.operation.datashader import rasterize

pn.extension("katex", nthreads=0)
hv.extension("bokeh")
opts.defaults(
    opts.Polygons(fill_alpha=0.2, line_color="red"),
    opts.VLine(color="black"),
    opts.Image(
        tools=["hover"],
        cmap="gray",  # specify color map
        invert_yaxis=True,
    ),
)


class ExpMeta(param.Parameterized):
    #
    instrument = param.Selector(default="CG1D", objects=["CG1D", "SNAP", "VENUS", "CUPID"], doc="Imageing instruments")
    #
    scan_name = param.String(
        default="my_scan",
        doc="user defined name for given CT scan",
    )
    #
    output_folder_name = param.String(
        default="my_recon",
        doc="output directory name for reconstruction results",
    )
    #
    IPTS = param.Integer(
        default=0,
        bounds=(0, 100_000_000),
        doc="experiment ID, a.k.a IPTS number",
    )
    #
    facility = param.String(
        default="HFIR",
        doc="facility hosting the instrument",
        precedence=-1,  # hide facility info from viewer
    )

    @param.depends("IPTS", watch=True)
    def _update_default_scan_name(self):
        if self.scan_name == "my_scan":
            self.scan_name = f"scan_{self.IPTS}"

    @param.depends("IPTS", "scan_name", watch=True)
    def _update_default_output_folder_name(self):
        if self.output_folder_name == "my_recon":
            if self.scan_name == "my_scan":
                self.output_folder_name = f"recon_{self.IPTS}"
            else:
                self.output_folder_name = f"recon_{self.scan_name}"

    @param.depends("instrument", watch=True)
    def _update_facility(self):
        if self.instrument in ("CG1D"):
            self.facility = "HFIR"
        elif self.instrument in ("SNAP", "VENUS"):
            self.facility = "SNS"
        elif self.instrument in ("CUPID"):
            self.facility = "STS"
        else:
            self.facility = "???"

    def panel(self):
        return pn.Param(
            self.param,
            name="Select instrument and input IPTS number",
            widgets={
                "instrument": pn.widgets.RadioButtonGroup,
                "IPTS": {
                    "widget_type": pn.widgets.LiteralInput,
                    "placeholder": "Enter your experiment IPTS number",
                },
            },
        )


class DataLoader(ExpMeta):
    proj_root = param.String(
        doc="project root directory",
        precedence=-1,  # hide facility info from viewer
    )
    ct_loaded = param.Boolean(
        default=False,
        doc="ct stack is loaded",
        # precedence=-1,
    )
    ob_loaded = param.Boolean(
        default=False,
        doc="ob stack is loaded",
        # precedence=-1,
    )
    df_loaded = param.Boolean(
        default=False,
        doc="df stack is loaded",
        # precedence=-1,
    )
    #
    load_data_button = pn.widgets.Button(name="Load data", button_type="primary")
    normalize_button = pn.widgets.Button(name="Normalize")

    def __init__(self):
        ExpMeta.__init__(self)
        self._update_proj_root()
        #
        self.load_data_button.on_click(self.load_to_memory)
        #
        self.ct = None
        self.ob = None
        self.df = None

    @param.depends("instrument", "IPTS", watch=True)
    def _update_proj_root(self):
        self.proj_root = f"~/tmp/{self.facility}/{self.instrument}/IPTS-{self.IPTS}"

    @param.depends("proj_root")
    def file_selector(self):
        self.radiograph_folder = pn.widgets.FileSelector(
            directory=self.proj_root,
            name="Radiographs(CT)",
        )
        self.openbeam = pn.widgets.FileSelector(
            directory=f"{self.proj_root}",
            name="Open-beam(OB)",
        )
        self.darkfield = pn.widgets.FileSelector(
            directory=f"{self.proj_root}",
            name="Dark-field(DF)",
        )
        return pn.Tabs(self.radiograph_folder, self.openbeam, self.darkfield)

    def read_tiffs(self, filelist):
        if len(filelist) == 0:
            return None
        # NOTE: there is a API issue with dxchange.read_tiff, which is using tifffile.imread
        #       incorrectly, so we are directly using tifffile for the moment until the issue
        #       is resolved.
        imgs = np.array([tifffile.imread(me) for me in filelist])
        imgs = hv.Dataset(
            (
                np.arange(imgs.shape[2]),
                np.arange(imgs.shape[1]),
                np.arange(imgs.shape[0]),
                imgs,
            ),
            ["x", "y", "n"],
            "count",
        )
        return imgs

    def load_to_memory(self, event):
        self.ct = self.read_tiffs(self.radiograph_folder.value)
        self.ob = self.read_tiffs(self.openbeam.value)
        self.df = self.read_tiffs(self.darkfield.value)
        #
        self.ct_loaded = False if self.ct is None else True
        self.ob_loaded = False if self.ob is None else True
        self.df_loaded = False if self.df is None else True

    @param.depends("ct_loaded", "ob_loaded", "df_loaded")
    def preview_pn(self):
        if self.ct is None:
            ct_pn = pn.pane.Markdown("no image to display")
        else:
            ct_pn = rasterize(self.ct.to(hv.Image, ["x", "y"], dynamic=True)).opts(
                opts.Image(
                    tools=["hover"],
                    cmap="gray",  # specify color map
                    invert_yaxis=True,
                )
            )
        #
        if self.ob is None:
            ob_pn = pn.pane.Markdown("no image to display")
        else:
            ob_pn = rasterize(self.ob.to(hv.Image, ["x", "y"], dynamic=True)).opts(
                opts.Image(
                    tools=["hover"],
                    cmap="gray",  # specify color map
                    invert_yaxis=True,
                )
            )
        #
        if self.df is None:
            df_pn = pn.pane.Markdown("no image to display")
        else:
            df_pn = rasterize(self.df.to(hv.Image, ["x", "y"], dynamic=True)).opts(
                opts.Image(
                    tools=["hover"],
                    cmap="gray",  # specify color map
                    invert_yaxis=True,
                )
            )
        return pn.Tabs(
            ("CT", ct_pn),
            ("OB", ob_pn),
            ("DF", df_pn),
        )

    def panel(self):
        #
        expmeta_pn = ExpMeta.panel(self)
        guide_pn = pn.Card(
            pn.pane.Markdown(
                """
                - The input data root directory **depends** on the instrument and IPTS number.
                - The scan name is used to locate the input radiographs.
                - All processing are **in memory**.
                """
            ),
            title="Guidelines",
            collapsed=True,
        )
        #
        action_pn = pn.Column(self.load_data_button, self.normalize_button)
        #
        control_pn = pn.Column(
            guide_pn,
            expmeta_pn,
            pn.layout.Divider(),
            action_pn,
        )
        return pn.Row(
            control_pn,
            pn.Column(
                self.file_selector,
                self.preview_pn,
            ),
            sizing_mode="stretch_width",
        )


# web app
dataloader = DataLoader()
dataloader_tab = ("Load Data", dataloader.panel())

roi_tab = ("ROI", pn.pane.Markdown("ROI"))
recon_tab = ("Reconstruction", pn.pane.Markdown("Reconstruction"))
viz_tab = ("Visualization", pn.pane.Markdown("Visualization"))

pn_app = pn.Tabs(
    dataloader_tab,
    roi_tab,
    recon_tab,
    viz_tab,
    tabs_location="left",
)

wizard = pn.template.FastListTemplate(
    site="iMars3D reconstruction demo",
    title="Neutron Image Reconstruction",
    logo="HFIR_SNS_logo.png",
    header_background="#00A170",
    main=pn_app,
    theme="dark",
    theme_toggle=True,
).servable()
