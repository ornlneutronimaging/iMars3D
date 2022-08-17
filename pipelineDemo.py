#!/usr/bin/env python3

import panel as pn
import holoviews as hv
from imars3dv2.widgets.metadata import MetaData
from imars3dv2.widgets.dataloading import DataLoader
from imars3dv2.widgets.selectroi import SelectROI
from imars3dv2.widgets.preprocess import Preprocess
from imars3dv2.widgets.reconstruction import Reconstruction
from imars3dv2.widgets.visualization import Visualization


pn.extension(
    "katex",
    nthreads=0,
    notifications=True,
)
hv.extension("bokeh")


# build the pipeline
wizard = pn.pipeline.Pipeline(
    stages=[
        ("Metadata", MetaData),
        ("Load Data", DataLoader),
        ("ROI selection", SelectROI),
        ("Preprocess", Preprocess),
        ("Reconstruction", Reconstruction),
        ("Visualization", Visualization),
    ],
    debug=True,
)
# NOTE: we have to disable the axes linking as it will try to link with
# the "ct" viewers in the pipeline.
wizard.network.linked_axes = False

# setup via template
pn.template.FastListTemplate(
    site="iMars3D demo",
    title="Neutron Image Reconstruction",
    logo="HFIR_SNS_logo.png",
    header_background="#00A170",
    main=wizard,
    # theme="dark",
    theme_toggle=True,
).servable()
