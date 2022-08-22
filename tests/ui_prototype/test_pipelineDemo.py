import pytest
from playwright.sync_api import Page, expect

timeout = 20000

@pytest.fixture(scope="function", autouse=True)
def setup_page(page: Page):
    page.set_default_timeout(timeout)
    page.goto("http://localhost:5006/pipelineDemo?theme=dark")
    expect(page).to_have_url("http://localhost:5006/pipelineDemo?theme=dark")

    # Click Next button
    page.locator("button:has-text(\"Next\")").click()
    yield page


def test_image_test(page: Page):
    # Click Open-beam(OB) tab
    page.locator("text=Open-beam(OB)").click()
    
    # Select file
    page.locator("text=0001.tif").nth(1).click()
    page.wait_for_timeout(200)

    # Move file to staging area
    page.locator("text=/.*\\>\\>.*/").nth(1).click()
    page.wait_for_timeout(200)

    # Click Load Button to load file
    page.locator("text=Load All").click()
    page.wait_for_timeout(200)

    # Click Next button
    page.locator("text=Next").click()
    
     # Click OB tab
    page.locator("text=OB").nth(1).click()
    
    # Click image canvas
    page.locator("div:nth-child(2) > div:nth-child(2) > div > div > div:nth-child(5)").first.click()
    
    expect(page.locator(".bk .bk-canvas-events").nth(1)).to_be_visible()
    
   
    
def test_region_selection_values(page: Page):
    # Click Open-beam(OB) tab
    page.locator("text=Open-beam(OB)").click()
    
    # Select file
    page.locator("text=0001.tif").nth(1).click()
    page.wait_for_timeout(200)

    # Move file to staging area
    page.locator("text=/.*\\>\\>.*/").nth(1).click()
    page.wait_for_timeout(200)

    # Click Load All button
    page.locator("text=Load All").click()
    page.wait_for_timeout(200)

    # Click Next button
    page.locator("text=Next").click()
    
     # Click OB tab
    page.locator("text=OB").nth(1).click()
    
    # Click on image canvas
    page.locator("div:nth-child(2) > div:nth-child(2) > div > div > div:nth-child(5)").first.click()
    
    # Get data values from point on image that was selected
    x_val = float(page.locator("span[data-value]").nth(0).inner_text())
    y_val = float(page.locator("span[data-value]").nth(1).inner_text())
    count_val = int(page.locator("span[data-value]").nth(2).inner_text())

    # Check values
    assert(x_val==49.500)
    assert(y_val==49.500)
    assert(count_val==20)