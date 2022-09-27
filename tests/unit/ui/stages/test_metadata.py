#!/usr/bin/env python3
import panel as pn
from panel.io.server import serve
from playwright.sync_api import Page, expect
from imars3d.ui.stages.metadata import MetaData


pn.extension("jsoneditor")

def test_metadata():
    # start the app
    app = pn.panel(MetaData().panel)
    serve(app, port=1960, threaded=True, show=True)
    pass


if __name__ == "__main__":
    test_metadata()