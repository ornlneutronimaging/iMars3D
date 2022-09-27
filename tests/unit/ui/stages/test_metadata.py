#!/usr/bin/env python3
import pytest
import shutil
import panel as pn
from pathlib import Path
from panel.io.server import serve
from playwright.sync_api import Page, expect
from imars3d.ui.stages.metadata import MetaData

pn.extension("jsoneditor")


@pytest.fixture(scope="module")
def port():
    return 1960


@pytest.fixture(scope="module")
def test_dir():
    # make tmp dir
    tmp_dir = Path.home() / Path("tmp/HFIR/CG1D/IPTS-11111")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    # shared/processed_data
    shared_dir = tmp_dir / Path("shared/processed_data")
    shared_dir.mkdir(parents=True, exist_ok=True)
    # raw
    raw_dir = tmp_dir / Path("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    yield str(tmp_dir)
    # cleanup
    shutil.rmtree(tmp_dir)


def test_example(page: Page, port:int, test_dir: str) -> None:
    # Serve the app
    app = pn.panel(MetaData().panel)
    serve(app, port=port, show=False, thread=True)

    # --- Test with Playwright ---
    # Go to http://localhost:port/
    page.goto(f"http://localhost:{port}/")

    # Select SNAP
    page.locator("select").select_option("SNAP")

    # Select CG1D
    page.locator("select").select_option("CG1D")

    # Click [placeholder="Enter non-standard project root manually here\.\.\."]
    page.locator("[placeholder=\"Enter non-standard project root manually here\\.\\.\\.\"]").click()

    # Fill [placeholder="Enter non-standard project root manually here\.\.\."]
    page.locator("[placeholder=\"Enter non-standard project root manually here\\.\\.\\.\"]").fill("/home")

    # Press Enter
    page.locator("[placeholder=\"Enter non-standard project root manually here\\.\\.\\.\"]").press("Enter")

    # Click [placeholder="Enter a name for your reconstruction\.\.\."]
    page.locator("[placeholder=\"Enter a name for your reconstruction\\.\\.\\.\"]").click()

    # Fill [placeholder="Enter a name for your reconstruction\.\.\."]
    page.locator("[placeholder=\"Enter a name for your reconstruction\\.\\.\\.\"]").fill("unittest")

    # Press Enter
    page.locator("[placeholder=\"Enter a name for your reconstruction\\.\\.\\.\"]").press("Enter")

    # Click input[type="text"] >> nth=0
    page.locator("input[type=\"text\"]").first.click()

    # Fill input[type="text"] >> nth=0
    page.locator("input[type=\"text\"]").first.fill("11111")

    # Press Enter
    page.locator("input[type=\"text\"]").first.press("Enter")

    # Click text=►CONFIG Viewer
    page.locator("text=►CONFIG Viewer").click()

    # Click .jsoneditor-expand-all
    page.locator(".jsoneditor-expand-all").click()

    # Click .jsoneditor-collapse-all
    page.locator(".jsoneditor-collapse-all").click()

    # Click text=▼CONFIG Viewer
    page.locator("text=▼CONFIG Viewer").click()

    # Click text=Save Config
    page.locator("text=Save Config").click()

    # verify that the config file is created
    config_file = Path(test_dir) / Path("shared/processed_data/unittest/unittest.json")
    assert config_file.exists()


if __name__ == "__main__":
    pytest.main([__file__])
