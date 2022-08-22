# UI Testing Requirements
In order to run Paywright tests, follow the latest installation guide at: https://playwright.dev/python/docs/intro.

If the link is unavailable, then there are a couple commands that you will run to setup Playwright. Open your terminal and run the following commands (Note: It doesn't matter which directory you are in for this step):

`pip install pytest-playwright`

`playwright install`

This should download the necessary packages including all of the currently available browsers for your system. Not all browsers are guranteed to work on every system, but at the very least, Chromium should be available for testing.

For running the tests in this directory, a file "0001.tif" needs to be copied into your home directory. Personally, I sourced a file from: https://github.com/ornlneutronimaging/testing_data

# Running Tests
In order to run tests, in your terminal, navigate to the directory that contains your tests files. There, you can simply use pytest.

`pytest`

This will run all of the tests that are found in the current directory. By default, Playwright tests will run in "headless" mode. This means that the user will not be able to see the tests running in an actual browser. Instead they will be run in the background. In order to visually inspect the tests as they are run, you can specify that you want the tests to be run in "headed" mode with the following option:

`pytest --headed`

This will pull up a browser window in which your tests will be run, and you can see all of the actions that Playwright is taking.

In order to switch to a different browser (the default is "Chromium"), you can specify the browser with the following:

`pytest --browser firefox --headed`

You can replace "firefox" with whichever browser you prefer that has been downloaded by playwright when you ran `playwright install`.

In order to run a specific test file you can just add the filename after the pytest invocation:

`pytest file.py`

Other options include:

Multiple test files:
`pytest file1.py file2.py`

Single test:
`pytest -k "test_within_file"`

Multiple browsers:
`pytest --browser chromium --browser webkit`

More information can be found in the Playwright docs: https://playwright.dev/python/docs/running-tests

# Writing Tests
## Basics
Like other Web GUI testing frameworks the basic workflow of writing a test in Playwright is to specify a "locator" (which is essentially a function that searches for specific elements on a web page and then returns that element), and then performing an action with the returned element. After an action is performed, you then write assertions that check to make sure that the functionality is working as intended. For example, say that there is a button on the web page with the text "Click me". Your locator would search for an element with the text "Click me" and upon finding that button return it. After you have a reference to that button you can simulate clicking that button. And then afterwards, you would check that the click performed it's expected function. Like if that button were supposed to turn the color of the background of the page to red, then you could use another locator to get the backround and check to see if it's color is red.

## Playwright Specifics
By default, Playwright has a Pytest fixture that sets up a browser and page object for each of your tests. Fixtures are essentially functions that you can reuse to do various things like setting and cleaning up tests easier, performing generic actions that should be shared across tests, etc. A basic test can start like this:

```python
from playwright.sync_api import Page, expect

def test_navigation(page: Page):
   page.goto("https://google.com")
   expect(page).to_have_url("https://google.com")

```

The page object has a variety of useful functions and will be your basis for doing actions in your test. Some common functions that page has include:

Locator (Note a guide on CSS selector can be found here: https://www.w3schools.com/cssref/css_selectors.asp)
`page.locator("some_selector")`

Navigation
`page.goto("url")`

Wait
`page.wait_for_timeout(300)`

A full list of the page functions can be found here: https://playwright.dev/python/docs/api/class-page

After using `page.locator()`, you will get an locator object back. You can do a variety of things with this object that will simulate a user interacting with the located element in their browser. Some common actions include:

Clicking an element
`locator.click()`

Dragging element
`locator.drag_to(dest)`

Flling element with text
`locator.fill(value)`

Return attribute
`locator.get_attribute(attribute_name)`

A full list of locator functions can be found here: https://playwright.dev/python/docs/api/class-locator

For developers familiar with Pytest, pretty much all of your Pytest features can apply to your Playwright tests.

## Codegen

Playwright has a useful feature to save *a lot* of time when writing tests called "Codegen". Running Codegen opens up a browser that you can interact with like you would any other browser. As you do things, another window will record all of your actions using the Playwright API including the selectors necessary to locate whatever elements you interact with as well as the actions you take on the elements. Codegen is installed alongside playwright automatically, and in order to run it simply use the following in your terminal:

`playwright codegen playwright.dev`

After you are finished you can copy the code into whatever file that you want, and even do things like change the language. More information is found here: https://playwright.dev/python/docs/codegen.
