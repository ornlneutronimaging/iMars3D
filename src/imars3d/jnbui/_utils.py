# coding: utf-8

import ipywidgets as ipyw
from IPython.display import display, HTML, clear_output

# standard
import sys

def js_alert(m):
    js = "<script>alert('%s');</script>" % m
    display(HTML(js))
    return


def encode(message, encoding='utf-8'):
    r"""
    Convert to message to bytes for python 2.X, otherwise do not convert

    Parameters
    ----------
    message : str
    encoding : str

    Returns
    -------
    str
    """
    if sys.version_info[0] < 3:
        return message.encode(encoding=encoding)
    return message

