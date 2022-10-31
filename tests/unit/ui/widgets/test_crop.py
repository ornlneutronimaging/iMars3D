#!/usr/bin/env python3
import pytest
import time
import panel as pn
import holoviews as hv
from panel.io.server import serve
from playwright.sync_api import Page
from imars3d.ui.widgets.crop import CropWidget

pn.extension("jsoneditor")
hv.extension("bokeh")


@pytest.fixture(scope="module")
def port():
    return 1958


def test_crop_page(page: Page, port: int):
    import skimage

    app = CropWidget(data=skimage.data.brain()[1])
    serve(app, port=port, show=False, thread=True)

    # Go to http://localhost:1958/
    page.goto("http://localhost:1958/")

    # Check input[type="checkbox"] >> nth=1
    page.locator('input[type="checkbox"]').nth(1).check()
    time.sleep(1)
    # Click div:nth-child(3) > div > div > button >> nth=0
    page.locator("div:nth-child(3) > div > div > button").first.click()
    time.sleep(1)
    # Click div:nth-child(5) > div > div > button >> nth=0
    page.locator("div:nth-child(5) > div > div > button").first.click()
    time.sleep(1)

    # Click text=Advanced Options
    page.locator("text=Advanced Options").click()
    time.sleep(1)

    # TEST ROI
    # Click div:nth-child(8)
    page.locator("div:nth-child(8)").click()
    time.sleep(1)
    # Double click div:nth-child(2) > div > div > div:nth-child(5) >> nth=0
    page.locator("div:nth-child(2) > div > div > div:nth-child(5)").first.dblclick()
    time.sleep(1)
    # Double click div:nth-child(2) > div > div > div:nth-child(5) >> nth=0
    page.locator("div:nth-child(2) > div > div > div:nth-child(5)").first.dblclick()
    time.sleep(1)
    # Check input[type="checkbox"] >> nth=1
    page.locator('input[type="checkbox"]').nth(1).check()
    time.sleep(1)

    task_entry = app.get_task_list()[0]
    print(task_entry)
    assert task_entry["inputs"]["array"] == "ct"
    assert task_entry["inputs"]["crop_limit"] == [127, 127, 127, 127]


if __name__ == "__main__":
    pytest.main([__file__])
