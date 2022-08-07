import param
import panel as pn

pn.extension("katex")


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

    def __init__(self):
        ExpMeta.__init__(self)
        self._update_proj_root()

    @param.depends("instrument", "IPTS", watch=True)
    def _update_proj_root(self):
        self.proj_root = f"~/tmp/{self.facility}/{self.instrument}/IPTS-{self.IPTS}"

    @param.depends("proj_root")
    def file_selector(self):
        self.radiograph_folder = pn.widgets.FileSelector(
            directory=self.proj_root,
            name="Radiographs",
        )
        self.openbeam = pn.widgets.FileSelector(
            directory=f"{self.proj_root}/ob",
            name="Open-beam",
        )
        self.darkfield = pn.widgets.FileSelector(
            directory=f"{self.proj_root}/df",
            name="Dark-field",
        )
        return pn.Tabs(self.radiograph_folder, self.openbeam, self.darkfield)

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
        control_pn = pn.Column(guide_pn, expmeta_pn)
        #
        return pn.Row(control_pn, self.file_selector, sizing_mode="stretch_width")


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
    theme_toggle=True,
).servable()
