#!/usr/bin/env python3

import param
import panel as pn
import holoviews as hv
from imars3dv2.widgets.dataloading import DataLoader
from imars3dv2.widgets.preprocess import Preprocess
from imars3dv2.widgets.selectroi import SelectROI

pn.extension(
    "katex",
    nthreads=0,
    notifications=True,
)
hv.extension("bokeh")


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
# NOTE: we have to disable the axes linking as it will try to link with
# the "ct" viewers in the pipeline.
pn_app.network.linked_axes = False

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
