"""
The main entry point for the back end software.

This can be invoked using

.. code-block:: sh

   python -m imars3d.backend <configfile>

The built-in help will give the options when supplied a ``--help`` flag.
"""
from imars3d.backend.workflow.engine import WorkflowEngineAuto
import logging
from pathlib import Path


def main(args=None):
    """Underlying entrypoint for the backend.

    The function args are exposed this way to allow for testing.
    Passing in None causes argparse to use ``sys.argv``.
    """
    # set up the command line parser
    import argparse

    parser = argparse.ArgumentParser(
        prog="imars3d.backend",
        description="Execute a workflow from a preconfigured json document",
        epilog="https://imars3d.readthedocs.io/en/latest/",
    )
    parser.add_argument("configfile", type=Path)
    parser.add_argument(
        "-l",
        "--log",
        nargs="?",
        default="info",
        choices=["debug", "info", "warn", "error"],
        help="The log level (default: %(default)s)",
    )
    # configure
    args = parser.parse_args(args)

    # configure logging
    logging.basicConfig()  # setup default handlers and formatting
    # override log level
    for handler in logging.getLogger().handlers:
        handler.setLevel(args.log.upper())
    logger = logging.getLogger("imars3d.backend")

    # run the workflow
    logger.info(f'Processing data using "{args.configfile}"')
    workflow = WorkflowEngineAuto(args.configfile)
    return workflow.run()


if __name__ == "__main__":
    import sys

    sys.exit(main())
