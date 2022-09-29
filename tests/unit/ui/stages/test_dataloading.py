#!/usr/bin/env python3
from cgi import test
import pytest
import shutil
import time
import panel as pn
from panel.io.server import serve
from playwright.sync_api import Page
from imars3d.ui.stages.dataloading import DataLoader

pn.extension("jsoneditor")


@pytest.fixture(scope="module")
def port():
    return 1957


@pytest.fixture(scope="module")
def ref_config():
    yield {
        "facility": "HFIR",
        "instrument": "CG1D",
        "ipts": 11111,
        "projectdir": "/tmp",
        "name": "unittest",
        "workingdir": "/tmp",
        "outputdir": "/tmp",
        "tasks": [],
    }
    # cleanup
    shutil.rmtree("/tmp/unittest.json", ignore_errors=True)


def test_loaddata_page(page: Page, port: int, ref_config: dict) -> None:
    # Serve the app
    dataloader = DataLoader(config_dict=ref_config)
    app = pn.panel(dataloader.panel)
    serve(app, port=port, show=False, thread=True)

    # Go to http://localhost:1957/
    page.goto("http://localhost:1957/")
    # Click text=Save Config so that we have something to load
    page.locator("text=Save Config").click()
    time.sleep(1)
    # Click [placeholder="Filter available options"] >> nth=0
    page.locator('[placeholder="Filter available options"]').first.click()
    # Fill [placeholder="Filter available options"] >> nth=0
    page.locator('[placeholder="Filter available options"]').first.fill("unittest.json")
    # Press Enter
    page.locator('[placeholder="Filter available options"]').first.press("Enter")
    # Click text=/.*\>\>.*/ >> nth=0
    page.locator("text=/.*\\>\\>.*/").first.click()
    # Click text=Update Config
    page.locator("text=Update Config").click()
    time.sleep(1)
    # Click text=Save Config so that we have something to load
    page.locator("text=Save Config").click()
    time.sleep(1)

    assert dataloader.config_dict["tasks"][0]["inputs"]["ct_files"][0] == "/tmp/unittest.json"


if __name__ == "__main__":
    pytest.main([__file__])
