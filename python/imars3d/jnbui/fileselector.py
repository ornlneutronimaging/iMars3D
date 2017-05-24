# coding: utf-8

import os, glob, time
import ipywidgets as ipyw
from IPython.display import display, HTML, clear_output
try:
    from ._utils import js_alert
except ValueError:
    from _utils import js_alert

class FileSelectorPanel:

    """Files and directories selector
    """
    
    select_layout = ipyw.Layout()
    button_layout = ipyw.Layout(margin="5px 40px")
    layout = ipyw.Layout()
    
    def __init__(self, instruction, start_dir=".", type='file', next=None, multiple=False):
        if not type in ['file', 'directory']:
            raise ValueError("type must be either file or directory")
        self.instruction = instruction
        self.type = type
        self.multiple = multiple
        self.createPanel(os.path.abspath(start_dir))
        self.next = next
        return
    
    
    def createPanel(self, curdir):
        self.curdir = curdir
        explanation = ipyw.Label(self.instruction)
        entries = sorted(os.listdir(curdir))
        entries = ['.', '..', ] + entries
        if self.multiple:
            widget = ipyw.SelectMultiple
            value = []
        else:
            widget = ipyw.Select
            value = entries[0]
        self.select = widget(
            value=value, options=entries,
            description="Select",
            layout = self.select_layout)
        # enter directory button
        self.enterdir = ipyw.Button(description='Enter directory', layout=self.button_layout)
        self.enterdir.on_click(self.handle_enterdir)
        # select button
        self.ok = ipyw.Button(description='Select', layout=self.button_layout)
        self.ok.on_click(self.validate)
        #
        buttons = ipyw.HBox(children=[self.enterdir, self.ok])
        self.widgets = [explanation, self.select, buttons]
        self.panel = ipyw.VBox(children=self.widgets, layout=self.layout)
        return
    
    
    def handle_enterdir(self, s):
        v = self.select.value
        if self.multiple:
            if len(v)!=1:
                js_alert("Please select on directory")
                return
            v = v[0]
        p = os.path.abspath(os.path.join(self.curdir, v))
        if os.path.isdir(p):
            self.remove()
            self.createPanel(p)
            self.show()
        return
    
    def validate(self, s):
        v = self.select.value
        # build paths
        if self.multiple:
            vs = v
            paths = [os.path.join(self.curdir, v) for v in vs]
        else:
            path = os.path.join(self.curdir, v)
            paths = [path]
        # check type
        if self.type == 'file':
            for p in paths:
                if not os.path.isfile(p):
                    js_alert("Please select file(s)")
                    return
        else:
            assert self.type == 'directory'
            for p in paths:
                if not os.path.isdir(p):
                    js_alert("Please select directory(s)")
                    return
        # set output
        if self.multiple:
            self.selected = paths
        else:
            self.selected = paths[0]
        # clean up
        self.remove()
        # next step
        if self.next:
            self.next()
        return

    def show(self):
        display(self.panel)

    def remove(self):
        for w in self.widgets: w.close()
        self.panel.close()





