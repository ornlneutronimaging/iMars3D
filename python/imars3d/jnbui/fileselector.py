# coding: utf-8

import os, glob, time
import ipywidgets as ipyw
from IPython.display import display, HTML, clear_output
try:
    from ._utils import js_alert
except Exception:
    from _utils import js_alert

class FileSelectorPanel:

    """Files and directories selector
    """
    
    #If ipywidgets version 5.3 or higher is used, the "width="
    #statement should change the width of the file selector. "width="
    #doesn't appear to work in earlier versions.
    select_layout = ipyw.Layout(width="750px")
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

    def format_file_time(self,ftime):
        fyear = int(ftime)/((60**2) * 24 * 366) + 1970
        fdy = (int(ftime) / ((60 ** 2) * 24)) - ((fyear - 1970) * 366)
        if 0 <= fdy <= 31:
            fmonth = "Jan"
            fday = fdy
        elif 32 <= fdy <= 59:
            fmonth = "Feb"
            fday = fdy - 32
        elif 60 <= fdy <= 90:
            fmonth = "Mar"
            fday = fdy - 60
        elif 91 <= fdy <= 120:
            fmonth = "Apr"
            fday = fdy - 91
        elif 121 <= fdy <= 151:
            fmonth = "May"
            fday = fdy - 121
        elif 152 <= fdy <= 181:
            fmonth = "June"
            fday = fdy - 152
        elif 182 <= fdy <= 212:
            fmonth = "July"
            fday = fdy - 182
        elif 213 <= fdy <= 243:
            fmonth = "August"
            fday = fdy - 213
        elif 244 <= fdy <= 273:
            fmonth = "Sept"
            fday = fdy - 244
        elif 274 <= fdy <= 304:
            fmonth = "Oct"
            fday = fdy - 274
        elif 305 <= fdy <= 334:
            fmonth = "Nov"
            fday = fdy - 305
        else:
            fmonth = "Dec"
            fday = fdy - 335
        fhr_exact = ((ftime / ((60 ** 2) * 24)) - ((fyear - 1970) * 366) - fdy) * 24
        fhr = int(fhr_exact)
        fmin = int((fhr_exact - fhr) * 60)
        if fmin < 10:
            fmin = "0" + str(fmin)
        else:
            fmin = str(fmin)
        ftime = fmonth + " " + str(fday) + ", " + str(fyear) + "  " + str(fhr) + ":" + fmin
        return (ftime)

    def create_file_time(self, entries):
        entries_ftime = [""]
        for f in entries:
            if os.path.isdir(f):
                entries_ftime.append("")
            else:
                ftime_sec = os.stat(f).st_mtime
                ftime = self.format_file_time(ftime_sec)
                entries_ftime.append(ftime)
        del entries_ftime[0]
        return(entries_ftime)
    
    def add_ftime_spacing(self, entries):
        max_len = 0
        for f in entries:
            if not os.path.isdir(f):
                if len(f) >= max_len:
                    max_len = len(f)
        base = "    |    "
        spacing = [""]
        dif = 0
        for f in entries:
            space = base
            if os.path.isdir(f):
                spacing.append("")
            else:
                dif = max_len - len(f)
                for i in range(0, dif):
                    space = " " + space
                spacing.append(space)
        del spacing[0]
        return(spacing)

    def create_nametime_labels(self, entries, spacing, ftime):
        label_list = [""]
        for f in entries:
            ind = entries.index(f)
            file_label = entries[ind] + spacing[ind] + ftime[ind]
            label_list.append(file_label)
        del label_list[0]
        return(label_list)

    def del_ftime(self, file_label):
        file_label_new = file_label
        if not os.path.isdir(file_label):
            for char in file_label:
                ind = file_label.index(char)
                if file_label[ind] == " " and file_label[ind + 1] == " ":
                    file_label_new = file_label[:ind]
                    break
        return(file_label_new)

    def createPanel(self, curdir):
        self.curdir = curdir
        explanation = ipyw.Label(self.instruction)
        entries_files = sorted(os.listdir(curdir))
        entries_spacing = self.add_ftime_spacing(entries_files)
        entries_paths = [os.path.join(curdir, e) for e in entries_files]
        entries_ftime = self.create_file_time(entries_paths)
        entries = self.create_nametime_labels(entries_files, entries_spacing, entries_ftime)
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
            layout=self.select_layout)
        # enter directory button
        self.enterdir = ipyw.Button(description='Enter directory', layout=self.button_layout)
        self.enterdir.on_click(self.handle_enterdir)
        # select button
        self.ok = ipyw.Button(description='Select', layout=self.button_layout)
        self.ok.on_click(self.validate)
        buttons = ipyw.HBox(children=[self.enterdir, self.ok])
        self.widgets = [explanation, self.select, buttons]
        self.panel = ipyw.VBox(children=self.widgets, layout=self.layout)
        return	
    
    def handle_enterdir(self, s):
        v = self.select.value
        v = self.del_ftime(v)
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
        v = self.del_ftime(v)
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
        display(HTML("""
        <html>
        <style type="text/css">
        div#notebook{
            font-family: "Lucida Console", Monaco, monospace;
        }
        </style>
        </html>"""))
        display(self.panel)

    def remove(self):
        for w in self.widgets: w.close()
        self.panel.close()


#def test1():
    #panel = FileSelectorPanel("instruction", start_dir=".")
    #panel.createPanel(".")
    #return


#def main():
    #test1()
    #return

#if __name__ == '__main__': main()



