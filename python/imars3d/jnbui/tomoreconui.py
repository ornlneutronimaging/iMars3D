# coding: utf-8

import os, subprocess, numpy as np
import ipywidgets as ipyw
import pickle as pkl
from ipywe import ImageDisplay, ImageSlider
from .ct_wizard import ct_wizard as ctw
from IPython.display import display, HTML, clear_output

remove_rings = None
smooth_recon = None
smooth_projection = None
curr_panel = None

def tomoReconStart(image_width=300, image_height=300, remove_rings_at_sinograms=False, smooth_rec=False, smooth_proj=False):
    global remove_rings, smooth_recon, smooth_projection, curr_panel
    remove_rings = remove_rings_at_sinograms
    smooth_recon = smooth_rec
    smooth_projection = smooth_proj
    curr_panel = ReconStartButtons(image_width=image_width, image_height=image_height)
    curr_panel.show()
    return curr_panel.ct, curr_panel.config

class ReconPanel:

    panel_layout = ipyw.Layout(border="1px lightgray solid", margin="5px", padding="15px")
    button_layout = ipyw.Layout(margin="10px 5px 5px 5px")
    label_layout = ipyw.Layout(height='35px', padding='8px', width='300px')

    def show(self):
        display(self.panel)

    def remove(self):
        for w in self.widgets: w.close()
        self.panel.close()

    def nextStep(self):
        raise NotImplementedError

class ReconStartButtons(ReconPanel):
    
    def __init__(self, image_width, image_height):
        self.img_width = image_width
        self.img_height = image_height
        self.widgets = None
        self.panel = None
        self.createButtons()
        return

    def createButtons(self):
        explanation = ipyw.Label("Do you wish to start from scratch or use a previous reconstruction configuration?", layout=self.label_layout)
        scratch_button = ipyw.Button(description="Start from Scratch", layout=self.button_layout)
        prev_button = ipyw.Button(description="Previous Config", layout=self.button_layout)
        buttons = ipyw.HBox(children=[scratch_button, prev_button])
        self.widgets = [explanation, buttons]
        scratch_button.on_click(self.nextStep)
        prev_button.on_click(self.reloadConfig)
        self.panel = ipyw.VBox(children=self.widgets, layout=self.panel_layout)
        return

    def nextStep(self):
        global curr_panel
        self.remove()
        curr_panel = ReconWizard(self.img_width, self.img_height)
        curr_panel.show()
        return

    def reloadConfig(self):
        config = pkl.load(open('/HFIR/CG1D/IPTS-15518/shared/processed_data/derek_inj/recon-config.pkl'))
        if not os.path.exists(config.outdir):
            os.makedirs(config.outdir)
        os.chdir(config.outdir)
        assert os.getcwd() == config.outdir
        pkl.dump(config, open('recon-config.pkl', 'wb'))
        for k, v in config.__dict__.items():
            if k.startswith('_'): continue
            sv = str(v)
            if len(sv) > 60:
                sv = sv[:50] + '...'
            print "{0:20}{1:<}".format(k,sv)
        global curr_panel
        self.remove()
        curr_panel = CTCreationPanel(self.img_width, self.img_height, config)
        curr_panel.show()
        return
        
class ReconWizard(ReconPanel):

    def __init__(self, image_width, image_height):
        self.img_width = image_width
        self.img_height = image_height
        self.config = None
        self.panel = None
        self.createWizardPanel()

    def createWizardPanel(self):
        self.config = ctw.config()
        ctw.wizard(self.config)
        self.saveConfig()

    def saveConfig(self):
        if not os.path.exists(self.config.outdir):
            os.makedirs(self.config.outdir)
        os.chdir(self.config.outdir)
        assert os.getcwd() == self.config.outdir
        pkl.dump(self.config, open('recon-config.pkl', 'wb'))
        for k, v in self.config.__dict__.items():
            if k.startswith('_'): continue
            sv = str(v)
            if len(sv) > 60:
                sv = sv[:50] + '...'
            print "{0:20}{1:<}".format(k,sv)
        self.nextStep()

    def nextStep(self):
        global curr_panel
        self.remove()
        curr_panel = CTCreationPanel(self.img_width, self.img_height, self.config)
        curr_panel.show()

class CTCreationPanel(ReconPanel):

    def __init__(self, image_width, image_height, config):
        self.img_width = image_width
        self.img_height = image_height
        self.config = config
        self.ct = None
        self.ppd = None
        self.panel = None
        self.createCT()
        return

    def createCT(self):
        from imars3d.CT import CT
        self.ct = CT(self.config.datadir, CT_subdir=self.config.ct_dir, CT_identifier=self.config.ct_sig, workdir=self.config.workdir, outdir=self.config.outdir, ob_files=self.config.ob_files, df_files=self.config.df_files) #ob_identifier=ob_sig, df_identifier=df_sig
        #Ignoring the %%time magics for now
        self.ppd = self.ct.preprocess()
        self.nextStep()

    def nextStep(self):
        global curr_panel
        self.remove()
        curr_panel = ImgSliderROIPanel(self.img_width, self.img_height, self.config, self.ct, self.ppd)
        curr_panel.show()

class ImgSliderROIPanel(ReconPanel):

    def __init__(self, image_width, image_height, config, ct, ppd):
        self.img_width = image_width
        self.img_height = image_height
        self.config = config
        self.ct = ct
        self.ppd = ppd
        self.panel = None
        self.ct_slider = None
        self.df_slider = None
        self.ob_slider = None
        self.roi_data = None
        self.createTabs()

    def createTabs(self):
        self.ct_slider = ImageSlider(self.ppd, self.img_width, self.img_height)
        self.df_slider = ImageSlider(self.ct.dfs, self.img_width, self.img_height)
        self.ob_slider = ImageSlider(self.ct.obs, self.img_width, self.img_height)
        explanation = ipyw.Label("Select a Region of Interest for the CT, DF, or OB Images", layout=self.label_layout)
        ct_button = ipyw.Button(description="Reconstruct", layout=self.button_layout)
        df_button = ipyw.Button(description="Reconstruct", layout=self.button_layout)
        ob_button = ipyw.Button(description="Reconstruct", layout=self.button_layout)
        ct_tab = ipyw.VBox(children=[self.ct_slider, ct_button], layout=self.panel_layout)
        df_tab = ipyw.VBox(children=[self.df_slider, df_button], layout=self.panel_layout)
        ob_tab = ipyw.VBox(children=[self.df_slider, df_button], layout=self.panel_layout)
        children = [ct_tab, df_tab, ob_tab]
        tab = ipyw.Tab(children=children)
        tab.set_title(0, "CT")
        tab.set_title(1, "DF")
        tab.set_title(2, "OB")
        ct_button.on_click(self.ct_select)
        df_button.on_click(self.df_select)
        ob_button.on_click(self.ob_select)
        self.panel = tab

    def ct_select(self):
        self.roi_data = [self.ct_slider._xcoord_absolute, self.ct_slider._xcoord_max_roi, self.ct_slider._ycoord_absolute, self.ct_slider._ycoord_max_roi]
        global curr_panel
        self.reomve()
        curr_panel = ImgDisplayPanel(self.ppd, self.img_width, self.img_height, self.ct, self.config, self.roi_data)
        curr_panel.show()

    def df_select(self):
        self.roi_data = [self.df_slider._xcoord_absolute, self.df_slider._xcoord_max_roi, self.df_slider._ycoord_absolute, self.df_slider._ycoord_max_roi]
        global curr_panel
        self.remove()
        curr_panel = ImgDisplayPanel(self.ct.dfs, self.img_width, self.img_height, self.ct, self.config, self.roi_data)
        curr_panel.show()

    def ob_select(self):
        self.roi_data = [self.ob_slider._xcoord_absolute, self.ob_slider._xcoord_max_roi, self.ob_slider._ycoord_absolute, self.ob_slider._ycoord_max_roi]
        global curr_panel
        self.remove()
        curr_panel = ImgDisplayPanel(self.ct.obs, self.img_width, self.img_height, self.ct, self.config, self.roi_data)
        curr_panel.show()

class ImgDisplayPanel(ReconPanel):

    def __init__(self, img_series, width, height, ct, config, roi_data):
        self.img_width = width
        self.img_height = height
        self.roi_data = roi_data
        self.ct = ct
        self.config = config
        self.img_disp = None
        self.avg_img = self.calc_avg(img_series)
        self.createImgDisplay()

    def calc_avg(self, img_series):
        num = len(img_series)
        img_data_series = []
        for img in img_series:
            img_data_series.append(img.data)
        sum_img = np.sum(img_data_series, axis=0)
        avg_img = sum_img / num
        return avg_img

    def createImgDisplay(self):
        self.img_disp = ImageDisplay(self.avg_img, self.img_width, self.img_height, init_roi=self.roi_data)
        explanation = ipyw.Label("Confirm ROI", layout=self.label_layout)
        recon_button = ipyw.Button(description="Reconstruct", layout=self.button_layout)
        children = [explanation, self.img_disp, recon_button]
        conf_pan = ipyw.VBox(children=children, layout=self.panel_layout)
        self.panel = conf_pan   
        recon_button.on_click(self.nextStep)

    def nextStep(self):
        xmin = self.img_disp._xcoord_absolute
        ymin = self.img_disp._ycoord_absolute
        xmax = self.img_disp._xcoord_max_roi
        ymax = self.img_disp._ycoord_max_roi
        self.ct.recon(crop_window=(xmin, ymin, xmax, ymax), remove_rings_at_sinograms=remove_rings, smooth_recon=smooth_recon, smooth_projection=smooth_projection)       
        print self.config.workdir

