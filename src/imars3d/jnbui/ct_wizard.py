# coding: utf-8
from ._utils import encode


def wizard(config=None, context=None):
    if context is None:
        context = Context()
    if config is None:
        config = Config()
    context.config = config
    WizardPanel(InstrumentPanel(context))
    return


import os, imars3d, numpy as np, glob, time
import ipywidgets as ipyw
from IPython.display import display, HTML, clear_output
from imars3d.jnbui._utils import js_alert


class Context:
    pass


class Config:
    def __init__(self, ipts=None, scan=None):
        self.ipts = ipts
        self.scan = scan


# keep the lowercase name for backward compatibility
config = Config


def close(w):
    "recursively close a widget"
    if hasattr(w, "children"):
        for c in w.children:
            close(c)
            continue
    w.close()
    return


class Panel(object):

    layout = ipyw.Layout(border="1px lightgray solid", margin="5px", padding="15px")
    button_layout = ipyw.Layout(margin="10px 5px 5px 5px")
    label_layout = ipyw.Layout(height="32px", padding="2px", width="300px")

    def show(self):
        display(self.panel)

    def remove(self):
        close(self.panel)

    def nextStep(self):
        raise NotImplementedError


class WizardPanel:

    label_layout = ipyw.Layout(height="35px", padding="8px", width="300px")

    def __init__(self, start_panel):
        display(ipyw.Label("Tomography reconstruction wizard", layout=self.label_layout))
        start_panel.show()
        return


class InstrumentPanel(Panel):

    instruments = {
        # vulcan: 'sns',
        "snap": "sns",
        "cg1d": "hfir",
    }

    def __init__(self, context):
        self.context = context
        explanation = ipyw.Label("Please choose the instrument", layout=self.label_layout)
        # self.text = ipyw.Text(value="CG1D", description="", placeholder="instrument name")
        self.text = ipyw.Select(value="CG1D", options=[i.upper() for i in self.instruments.keys()])
        ok = ipyw.Button(description="OK", layout=self.button_layout)
        ok.on_click(self.validate)
        skip = ipyw.Button(description="Skip", layout=self.button_layout)
        skip.on_click(self.skip)
        buttons = ipyw.HBox(children=(ok, skip))
        self.widgets = [explanation, self.text, buttons]
        self.panel = ipyw.VBox(children=self.widgets, layout=self.layout)

    def validate(self, s):
        instrument = encode(self.text.value)
        if instrument.lower() not in self.instruments.keys():
            s = "instrument %s not supported!" % instrument
            js_alert(s)
        else:
            self.context.config.instrument = instrument.upper()
            self.context.config.facility = self.instruments[instrument.lower()].upper()
            self.nextStep()
        return

    def nextStep(self):
        self.remove()
        ipts_panel = IPTSpanel(self.context)
        ipts_panel.show()
        return

    def skip(self, s):
        self.context.config.instrument = None
        self.context.config.facility = None
        self.nextStep()
        return


class IPTSpanel(Panel):
    def __init__(self, context):
        self.context = context
        explanation = ipyw.Label("Please input your experiment IPTS number", layout=self.label_layout)
        self.text = ipyw.Text(value="", description="IPTS-", placeholder="IPTS number")
        self.ok = ipyw.Button(description="OK", layout=self.button_layout)
        self.ok.on_click(self.validate_IPTS)
        skip = ipyw.Button(description="Skip", layout=self.button_layout)
        skip.on_click(self.skip)
        buttons = ipyw.HBox(children=(self.ok, skip))
        self.widgets = [explanation, self.text, buttons]
        self.panel = ipyw.VBox(children=self.widgets, layout=self.layout)

    def validate_IPTS(self, s):
        ipts1 = encode(self.text.value)
        facility = self.context.config.facility
        instrument = self.context.config.instrument
        path = os.path.abspath("/%s/%s/IPTS-%s" % (facility, instrument, ipts1))
        if not os.path.exists(path):
            s = "Cannot open directory %s ! Please check IPTS number" % path
            js_alert(s)
        else:
            self.context.config.ipts = ipts = ipts1
            # use your experiment IPTS number
            self.context.config.iptsdir = iptsdir = path
            # path to the directory with ct, ob, and df data files or subdirs
            datadir = self.context.config.datadir = os.path.join(iptsdir, "raw/")
            # make sure there is ct scan directory
            self.context.config.ct_scan_root = ct_scan_root = os.path.join(datadir, "ct_scans")
            ct_scan_subdirs = [d for d in os.listdir(ct_scan_root) if os.path.isdir(os.path.join(ct_scan_root, d))]
            self.context.config.ct_scan_subdirs = ct_scan_subdirs
            self.nextStep()
        return

    def nextStep(self):
        self.remove()
        scan_panel = ScanNamePanel(self.context)
        scan_panel.show()
        return

    def skip(self, s):
        self.context.config.ipts = None
        self.context.config.iptsdir = os.path.expanduser("~")
        self.context.config.datadir = os.path.expanduser("~")
        self.context.config.ct_scan_root = os.path.expanduser("~")
        self.context.config.ct_scan_subdirs = []
        self.nextStep()
        return


class ScanNamePanel(Panel):
    def __init__(self, context):
        self.context = context
        explanation = ipyw.Label("Please give your neutron CT scan a name:", layout=self.label_layout)
        self.text = ipyw.Text(value="", description="Scan: ", placeholder="name of scan")
        self.ok = ipyw.Button(description="OK", layout=self.button_layout)
        self.widgets = [explanation, self.text, self.ok]
        self.ok.on_click(self.validate)
        self.panel = ipyw.VBox(children=self.widgets, layout=self.layout)

    def validate(self, s):
        v = self.text.value
        if not v:
            s = "Please specify a name for your tomography scan"
            js_alert(s)
        else:
            self.context.config.scan = encode(v)
            self.remove()
            wd_panel = WorkDirPanel(self.context, self.context.config.scan)
            wd_panel.show()
        return


class SelectDirPanel(Panel):
    def __init__(self, initial_guess, explanation=""):
        self.createSelectDirPanel(initial_guess, explanation)
        self.createRemovalAlertPanel()

    def createSelectDirPanel(self, initial_guess, explanation):
        # panel for soliciting work dir name
        explanation_label = ipyw.HTML("<p>" + explanation + "</p>")
        self.path_field = ipyw.Text(value=initial_guess)
        ok = ipyw.Button(description="OK", layout=self.button_layout)
        widgets = [explanation_label, self.path_field, ok]
        ok.on_click(self.validate)
        self.selectdir_panel = ipyw.VBox(children=widgets, layout=self.layout)

    def createRemovalAlertPanel(self):
        # panel for remove old dir
        alert = self.alert = ipyw.Label("** Warning: We are about to remove directory", layout=self.label_layout)
        self.pathtext = ipyw.HTML("")
        self.alert_banner = ipyw.HBox(children=[self.alert, self.pathtext])
        layout = ipyw.Layout(width="240px", padding="10px")
        yes = ipyw.Button(description="Yes. Please remove the directory", layout=layout)
        no = ipyw.Button(description="No. Let me choose a different directory", layout=layout)
        yes.on_click(self.removeSelectedDir)
        no.on_click(self.askForDir)
        self.removalalert_panel = ipyw.VBox(children=[self.alert_banner, yes, no])
        return

    def removeSelectedDir(self, s):
        self.remove()
        wait = ipyw.HTML(value="<p>Removing. Please wait...</p>")
        display(wait)
        time.sleep(0.2)
        import shutil

        if os.path.islink(self.path_candidate):
            os.unlink(self.path_candidate)
        else:
            try:
                shutil.rmtree(self.path_candidate)
            except:
                wait.close()
                js_alert("Unable to remove directory tree %s" % self.path_candidate)
                self.askForDir(s)
                return
        wait.close()
        self.selected = self.path_candidate
        self.nextStep()
        return

    def askForDir(self, s):
        self.removalalert_panel.layout.display = "none"
        self.selectdir_panel.layout.display = "flex"
        return

    def show(self):
        display(self.selectdir_panel, self.removalalert_panel)
        self.removalalert_panel.layout.display = "none"

    def remove(self):
        self.selectdir_panel.close()
        self.removalalert_panel.close()

    def compute_path_from_input(self):
        return self.path_field.value

    def validate(self, s):
        self.path_candidate = p = self.compute_path_from_input()
        if os.path.exists(p):
            # print "already exists"
            self.pathtext.value = '"%s"' % p
            self.removalalert_panel.layout.display = "flex"
            self.selectdir_panel.layout.display = "none"
        else:
            self.selected = p
            self.remove()
            # print "selected: %s" % self.selected
            self.nextStep()
        return


class WorkDirPanel(SelectDirPanel):

    layout = ipyw.Layout()

    def __init__(self, context, initial_guess):
        self.context = context
        # fast disk
        import getpass

        username = getpass.getuser()
        root = "/SNSlocal2/%s" % username
        if not os.path.exists(root):
            try:
                os.makedirs(root)
            except:
                root = os.path.expanduser("~/work.imars3d")
                if not os.path.exists(root):
                    os.makedirs(root)
        self.root = root
        self._check_space()
        explanation = (
            "Please pick a name for your temporary working directory. Usually it is the same as the name of your CT scan. But you can use a different one if you want to. The directory will be created under %s"
            % self.root
        )
        SelectDirPanel.__init__(self, initial_guess, explanation)
        self.path_field.description = "Workdir: "
        self.path_field.placeholder = "under %s" % self.root

    def compute_path_from_input(self):
        v = self.path_field.value
        return os.path.join(self.root, v)

    def nextStep(self):
        self.context.config.workdir = self.selected
        output_panel = OutputDirPanel(self.context, self.context.config.scan)
        output_panel.show()

    def _check_space(self):
        free_in_G = get_space(self.root)
        if free_in_G < 200:
            js_alert("%s only has %s GB left. Reconstruction may encounter problems." % (self.root, int(free_in_G)))


def get_space(path):
    if not os.path.exists(path):
        return get_space(os.path.dirname(path))
    stat = os.statvfs(path)
    return stat.f_frsize * stat.f_bavail / 1.0e9  # Gigabytes


class OutputDirPanel(SelectDirPanel):

    layout = ipyw.Layout()

    def __init__(self, context, initial_guess):
        self.context = context
        config = self.context.config
        self.root = os.path.join(config.iptsdir, "shared/processed_data/")
        explanation = (
            "Please pick a name for reconstruction output directory. Usually it is the same as the name of your CT scan. But you can use a different one if you want to. The directory will be created under %s"
            % self.root
        )
        SelectDirPanel.__init__(self, initial_guess, explanation)
        self.path_field.description = "Output dir: "
        self.path_field.placeholder = "under %s" % self.root

    def compute_path_from_input(self):
        v = self.path_field.value
        return os.path.join(self.root, v)

    def nextStep(self):
        self.context.config.outdir = self.selected
        ctdir_panel = CTDirPanel(self.context)
        ctdir_panel.show()

    pass


class CTDirPanel(Panel):
    def __init__(self, context):
        self.context = context
        # by standard, ct directories must be inside IPTS/raw/ct_scans, but older IPTS may not conform
        # in that case, a general directory selector is used
        config = context.config
        if not config.ct_scan_subdirs:
            return self.createDirSelector()
        # standard case
        explanation = ipyw.HTML("Please choose the sub-directory that contains the image files for your CT scan")
        self.select = ipyw.Select(
            options=config.ct_scan_subdirs, value=config.ct_scan_subdirs[0], description="CT scans"
        )
        self.ok = ipyw.Button(description="Select", layout=self.button_layout)
        self.use_dir_selector = ipyw.Button(
            description="If you cannot find your CT scan above, click me instead",
            layout=ipyw.Layout(margin="0 0 0 200px", width="350px"),
        )
        self.widgets = [explanation, self.select, self.ok, self.use_dir_selector]
        self.ok.on_click(self.validate)
        self.use_dir_selector.on_click(self.switchToDirSelector)
        self.panel = ipyw.VBox(children=self.widgets, layout=self.layout)

    def validate(self, s):
        self.context.config.ct_subdir = encode(self.select.value)
        self.remove()
        self.nextStep()
        return

    def switchToDirSelector(self, s):
        self.remove()
        self.createDirSelector()
        self.show()
        return

    def nextStep(self):
        next = CTSigPanel(self.context)
        next.show()
        return

    def createDirSelector(self):
        config = self.context.config
        # create file selector
        from .fileselector import FileSelectorPanel as FSP

        self.fsp = FSP("Please select the CT directory", start_dir=config.iptsdir, type="directory")
        # the call back function for the file selector
        def next(s):
            self.context.config.ct_subdir = self.fsp.selected
            self.nextStep()
            return

        self.fsp.next = next
        # show() method needs self.panel
        self.panel = self.fsp.panel
        return


class CTSigPanel(Panel):
    def __init__(self, context):
        self.context = context
        ct_sig, sample = self.calculate()
        explanation1 = ipyw.HTML(
            "<p>A signature word for filenames of the CT scan is needed.</p>"
            + "<p>The following is our best guess.</p>"
        )
        explanation2 = ipyw.HTML(
            "<p>If it does not work, please try to come up with a string that is common in all files of the CT scan of interests.</p>"
            + "<p>Here are some random samples of CT filenames:</p>"
        )
        samples = [ipyw.HTML(s) for s in sample]
        sample_panel = ipyw.VBox(
            children=samples,
            layout=ipyw.Layout(padding="20px", height="120px", width="600px", overflow_x="auto", overflow_y="auto"),
        )
        self.text = ipyw.Text(value=ct_sig, description="CT signature", layout=ipyw.Layout(margin="20px"))
        self.ok = ipyw.Button(description="OK", layout=self.button_layout)
        self.widgets = [explanation1, self.text, explanation2, sample_panel, self.ok]
        self.ok.on_click(self.validate)
        self.panel = ipyw.VBox(children=self.widgets, layout=self.layout)

    def calculate(self):
        context = self.context
        config = context.config
        # all files
        if os.path.isabs(config.ct_subdir):
            ct_dir = config.ct_subdir
        else:
            ct_dir = os.path.join(config.ct_scan_root, config.ct_subdir)
        config.ct_dir = ct_dir
        ct_files = os.listdir(ct_dir)
        # assume all files start with date like 20160918
        files_without_dates = [f[9:] for f in ct_files]
        # find common prefix
        ct_sig0 = os.path.commonprefix(files_without_dates).strip()
        ct_sig = "_".join(ct_sig0.split("_")[:-2])
        #  Example CT scan filenames
        indexes = np.random.choice(len(ct_files), 10)
        sample = [ct_files[i] for i in indexes]
        return ct_sig, sample

    def validate(self, s):
        self.context.config.ct_sig = encode(self.text.value)
        self.remove()
        self.nextStep()
        return

    def nextStep(self):
        next = OBPanel(self.context)
        next.show()
        return


class OBPanel(Panel):
    def __init__(self, context):
        self.context = context
        all_obs = self.calculate()
        # by standard, ob files must be inside IPTS/raw/OB, but older IPTS may not conform.
        # in that case, a general file selector is used
        if not all_obs:
            return self.createOBFilesSelector()
        # select files at standard place
        explanation1 = ipyw.HTML(
            "Open beam (OB) measurements are needed for normalization. "
            "Please select the OB files from below."
            "Use Shift-click or Ctrl-click to select multiple files"
        )
        self.select = ipyw.SelectMultiple(
            value=[], options=all_obs, description="OB files", layout=ipyw.Layout(margin="20px", width="600px")
        )
        self.ok = ipyw.Button(description="OK", layout=self.button_layout)
        self.ok.on_click(self.validate)
        # button to switch over to arbitrary files selector
        self.use_arbitrary_files_selector = ipyw.Button(
            description="If you cannot find your OB files above, click me instead",
            layout=ipyw.Layout(margin="0 0 0 200px", width="350px"),
        )
        self.use_arbitrary_files_selector.on_click(self.switchToFilesSelector)
        #
        self.widgets = [explanation1, self.select, self.ok, self.use_arbitrary_files_selector]
        self.panel = ipyw.VBox(children=self.widgets, layout=self.layout)

    def calculate(self):
        config = self.context.config
        # all files
        config.ob_dir = ob_dir = os.path.join(config.datadir, "ob")
        if not os.path.exists(ob_dir):
            return
        exts = [".fits", ".tif", ".tiff"]
        files = []
        for f in os.listdir(ob_dir):
            b, ext = os.path.splitext(f)
            if ext in exts:
                files.append(f)
            continue
        return files

    def validate(self, s):
        v = [encode(i) for i in self.select.value]
        if not v:
            js_alert("Please select at least one OB file")
            return
        config = self.context.config
        config.ob_files = [os.path.join(config.ob_dir, f) for f in v]
        self.remove()
        self.nextStep()
        return

    def switchToFilesSelector(self, s):
        self.remove()
        self.createOBFilesSelector()
        self.show()
        return

    def nextStep(self):
        next = DFPanel(self.context)
        next.show()
        return

    def createOBFilesSelector(self):
        config = self.context.config
        # create file selector
        from .fileselector import FileSelectorPanel as FSP

        self.fsp = FSP("OB files", start_dir=config.iptsdir, type="file", multiple=True)
        # call back function
        def next(s):
            self.context.config.ob_files = self.fsp.selected
            self.nextStep()
            return

        self.fsp.next = next
        # show() method need self.panel
        self.panel = self.fsp.panel
        return


class DFPanel(Panel):
    def __init__(self, context):
        self.context = context
        all_dfs = self.calculate()
        # by standard, df files must be inside IPTS/raw/DF, but older IPTS may not conform.
        # in that case, a general file selector is used
        if not all_dfs:
            return self.createDFFilesSelector()
        # select files at standard place
        explanation1 = ipyw.HTML(
            "Dark field (DF) measurements are needed for background correction. "
            "Please select the DF files from below. "
            "Use Shift-click or Ctrl-click to select multiple files"
        )
        self.select = ipyw.SelectMultiple(
            value=[], options=all_dfs, description="DF files", layout=ipyw.Layout(margin="20px", width="600px")
        )
        self.ok = ipyw.Button(description="OK", layout=ipyw.Layout(margin="20px"))
        self.ok.on_click(self.validate)
        # button to switch to arbitrary files selector
        self.use_arbitrary_files_selector = ipyw.Button(
            description="If you cannot find your DF files above, click me instead",
            layout=ipyw.Layout(margin="0 0 0 200px", width="350px"),
        )
        self.use_arbitrary_files_selector.on_click(self.switchToFilesSelector)
        #
        self.widgets = [self.createSkipButton(), explanation1, self.select, self.ok, self.use_arbitrary_files_selector]
        self.panel = ipyw.VBox(children=self.widgets, layout=self.layout)

    def createSkipButton(self):
        skip_DF = ipyw.Button(description="Skip dark field files", layout=ipyw.Layout(margin="20px", width="180px"))
        skip_DF.on_click(self.onSkipDF)
        return skip_DF

    def calculate(self):
        config = self.context.config
        # all files
        config.df_dir = df_dir = os.path.join(config.datadir, "df")
        if not os.path.exists(df_dir):
            return
        exts = [".fits", ".tif", ".tiff"]
        files = []
        for f in os.listdir(df_dir):
            b, ext = os.path.splitext(f)
            if ext in exts:
                # p = os.path.join(df_dir, f)
                # t = time.ctime(os.path.getmtime(p))
                # s = '%s: %s' % (f, t)
                # files.append(s)
                files.append(f)
            continue
        return files

    def validate(self, s):
        v = [encode(i) for i in self.select.value]
        if not v:
            js_alert("Please select at least one DF file")
            return
        config = self.context.config
        config.df_files = [os.path.join(config.df_dir, f) for f in v]
        self.remove()
        self.nextStep()
        return

    def switchToFilesSelector(self, s):
        self.remove()
        self.createDFFilesSelector()
        self.show()
        return

    def onSkipDF(self, s):
        config = self.context.config
        config.skip_df = True
        config.df_files = None
        self.remove()
        self.nextStep()
        return

    def nextStep(self):
        print("Configuration done!")
        return

    def remove(self):
        if hasattr(self, "fsp"):
            self.fsp.remove()
        super(DFPanel, self).remove()
        return

    def createDFFilesSelector(self):
        config = self.context.config
        # create file selector
        from .fileselector import FileSelectorPanel as FSP

        self.fsp = FSP("DF files", start_dir=config.iptsdir, type="file", multiple=True)
        # call back function
        def next(s):
            self.context.config.df_files = self.fsp.selected
            self.remove()
            self.nextStep()
            return

        self.fsp.next = next
        # show() method need self.panel
        # self.panel = self.fsp.panel
        self.panel = ipyw.VBox(children=(self.createSkipButton(), self.fsp.panel), layout=self.layout)
        return


# WizardPanel(DFPanel(config))
# WizardPanel(IPTSpanel(config))
