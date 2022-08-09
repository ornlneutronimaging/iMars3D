#!/usr/bin/env python3

import param
import panel as pn
import holoviews as hv
from holoviews import opts

from imars3dv2.widgets.dataloading import DataLoader
from imars3dv2.widgets.preprocess import Preprocess


pn.extension(
    "katex",
    nthreads=0,
    notifications=True,
)
hv.extension("bokeh")
opts.defaults(
    opts.GridSpace(shared_xaxis=True, shared_yaxis=True),
    opts.Image(cmap="viridis", width=400, height=400),
    # opts.Labels(text_color='white', text_font_size='8pt', text_align='left', text_baseline='bottom'),
    opts.Path(color="white"),
    opts.Spread(width=600),
    opts.Overlay(show_legend=False),
)


class SelectROI(param.Parameterized):
    # container to store images
    ct = param.Array(
        doc="radiograph stack as numpy array",
        precedence=-1,  # hide
    )

    @param.output(
        ("ct", param.Array),
    )
    def get_data(self):
        return self.ct

    def panel(self):
        return pn.pane.Markdown("**TBD**: Select ROI")


class Reconstruction(param.Parameterized):
    # container to store images
    ct = param.Array(
        doc="radiograph stack as numpy array",
        precedence=-1,  # hide
    )
    recon = param.Array(
        doc="reconstruction results as numpy array",
        precedence=-1,  # hide
    )

    @param.output(
        ("recon", param.Array),
    )
    def get_data(self):
        return self.recon

    def panel(self):
        return pn.pane.Markdown("**TBD**: Reconstruction")


class Visualization(param.Parameterized):
    # container to store images
    recon = param.Array(
        doc="reconstruction results as numpy array",
        precedence=-1,  # hide
    )

    def panel(self):
        return pn.pane.Markdown("**TBD**: Visualization")


# build the pipeline
pn_app = pn.pipeline.Pipeline(
    stages=[
        ("Load Data", DataLoader),
        ("Preprocess", Preprocess),
        ("ROI selection", SelectROI),
        ("Reconstruction", Reconstruction),
        ("Visualization", Visualization),
    ],
    debug=True,
)

# setup via template
wizard = pn.template.FastListTemplate(
    site="iMars3D demo",
    title="Neutron Image Reconstruction",
    logo="HFIR_SNS_logo.png",
    header_background="#00A170",
    main=pn_app,
    # theme="dark",
    theme_toggle=True,
).servable()
