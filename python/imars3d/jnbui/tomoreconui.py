# coding: utf-8

import os
#import subprocess
import numpy as np
import ipywidgets as ipyw
import pickle as pkl
from ipywe import imagedisplay as imgd, imageslider as imgs
#from .ct_wizard 
import ct_wizard as ctw
from IPython.display import display #, HTML, clear_output

select_next = -1

def tomoReconStart(image_width=300, image_height=300, remove_rings_at_sinograms=False, smooth_rec=False, smooth_proj=False):
    global select_next
    img_width = image_width
    img_height = image_height
    remove_rings = remove_rings_at_sinograms
    smooth_recon = smooth_rec
    smooth_projection = smooth_proj
    start_pan = ReconStartButtons()
    start_pan.show()
    if select_next == 0:
        config = start_pan.config
        start_pan.remove()
    elif select_next == 1:
        start_pan.remove()
        wizard = ReconWizard()
        wizard.show()
        config = wizard.config
        wizard.remove()
    else:
        print("A button was not clicked before the code continued")
        raise ValueError
    ct_create = CTCreationPanel(config)
    ct = ct_create.ct
    ppd = ct_create.ppd
    select_next = -1
    img_slide = ImgSliderROIPanel(img_width, img_height, ct, ppd)
    img_slide.show()
    roi = img_slide.roi_data
    if select_next == 0:
        img_slide.remove()
        img_disp = ImgDisplayPanel(ppd, img_width, img_height, ct, config, roi, remove_rings, smooth_recon, smooth_projection)
        img_disp.show()
    elif select_next == 1:
        img_slide.remove()
        img_disp = ImgDisplayPanel(ct.dfs, img_width, img_height, ct, config, roi, remove_rings, smooth_recon, smooth_projection)
        img_disp.show()
    elif select_next == 2:
        img_slide.remove()
        img_disp = ImgDisplayPanel(ct.obs, img_width, img_height, ct, config, roi, remove_rings, smooth_recon, smooth_projection)
        img_disp.show()
    else:
        print("The code continued before a recon button was clicked.")
        raise ValueError
    ct = img_disp.ct
    img_disp.remove()
    return config, ct

class ReconPanel:

    panel_layout = ipyw.Layout(border="1px lightgray solid", margin="5px", padding="15px")
    button_layout = ipyw.Layout(margin="10px 5px 5px 5px")
    label_layout = ipyw.Layout(height='35px', padding='8px', width='300px')

    def show(self):
        display(self.panel)

    def remove(self):
        for w in self.widgets: w.close()
        self.panel.close()

class ReconStartButtons(ReconPanel):
    
    def __init__(self):
        self.widgets = None
        self.panel = None
        self.config = None
        self.createButtons()
        return

    def createButtons(self):
        explanation = ipyw.Label("Do you wish to start from scratch or use a previous reconstruction configuration?", layout=self.label_layout)
        scratch_button = ipyw.Button(description="Start from Scratch", layout=self.button_layout)
        prev_button = ipyw.Button(description="Previous Config", layout=self.button_layout)
        buttons = ipyw.HBox(children=[scratch_button, prev_button])
        self.widgets = [explanation, buttons]
        scratch_button.on_click(self.prepWizard)
        prev_button.on_click(self.reloadConfig)
        self.panel = ipyw.VBox(children=self.widgets, layout=self.panel_layout)
        return

    def reloadConfig(self):
        self.config = pkl.load(open('/HFIR/CG1D/IPTS-15518/shared/processed_data/derek_inj/recon-config.pkl'))
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
        return

    def prepWizard(self):
        global select_next
        select_next = 1
        
class ReconWizard(ReconPanel):

    def __init__(self):
        self.config = None
        self.panel = None
        self.createWizardPanel()

    def createWizardPanel(self):
        self.config = ctw.config()
        pan = ctw.wizard(self.config)
        pan
        self.widgets = [pan]
        self.panel = ipyw.VBox(children=self.widgets)
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

class CTCreationPanel(ReconPanel):

    def __init__(self, config):
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

class ImgSliderROIPanel(ReconPanel):

    def __init__(self, image_width, image_height, ct, ppd):
        self.img_width = image_width
        self.img_height = image_height
        self.ct = ct
        self.ppd = ppd
        self.panel = None
        self.ct_slider = None
        self.df_slider = None
        self.ob_slider = None
        self.roi_data = None
        self.createTabs()

    def createTabs(self):
        self.ct_slider = imgs.ImageSlider(self.ppd, self.img_width, self.img_height)
        self.df_slider = imgs.ImageSlider(self.ct.dfs, self.img_width, self.img_height)
        self.ob_slider = imgs.ImageSlider(self.ct.obs, self.img_width, self.img_height)
        explanation = ipyw.Label("Select a Region of Interest for the CT, DF, or OB Images", layout=self.label_layout)
        ct_button = ipyw.Button(description="Reconstruct", layout=self.button_layout)
        df_button = ipyw.Button(description="Reconstruct", layout=self.button_layout)
        ob_button = ipyw.Button(description="Reconstruct", layout=self.button_layout)
        ct_tab = ipyw.VBox(children=[self.ct_slider, ct_button], layout=self.panel_layout)
        df_tab = ipyw.VBox(children=[self.df_slider, df_button], layout=self.panel_layout)
        ob_tab = ipyw.VBox(children=[self.df_slider, df_button], layout=self.panel_layout)
        self.widgets = [ct_tab, df_tab, ob_tab]
        self.panel = ipyw.Tab(children=self.widgets)
        self.panel.set_title(0, "CT")
        self.panel.set_title(1, "DF")
        self.panel.set_title(2, "OB")
        ct_button.on_click(self.ct_select)
        df_button.on_click(self.df_select)
        ob_button.on_click(self.ob_select)

    def ct_select(self):
        self.roi_data = [self.ct_slider._xcoord_absolute, self.ct_slider._xcoord_max_roi, self.ct_slider._ycoord_absolute, self.ct_slider._ycoord_max_roi]
        global select_next
        select_next = 0

    def df_select(self):
        self.roi_data = [self.df_slider._xcoord_absolute, self.df_slider._xcoord_max_roi, self.df_slider._ycoord_absolute, self.df_slider._ycoord_max_roi]
        global select_next
        select_next = 1

    def ob_select(self):
        self.roi_data = [self.ob_slider._xcoord_absolute, self.ob_slider._xcoord_max_roi, self.ob_slider._ycoord_absolute, self.ob_slider._ycoord_max_roi]
        global select_next
        select_next = 2

class ImgDisplayPanel(ReconPanel):

    def __init__(self, img_series, width, height, ct, config, roi_data, remove_rings, smooth_rec, smooth_proj):
        self.img_width = width
        self.img_height = height
        self.roi_data = roi_data
        self.ct = ct
        self.config = config
        self.remove_rings = remove_rings
        self.smooth_recon = smooth_rec
        self.smooth_projection = smooth_proj
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
        self.img_disp = imgd.ImageDisplay(self.avg_img, self.img_width, self.img_height, init_roi=self.roi_data)
        explanation = ipyw.Label("Confirm ROI", layout=self.label_layout)
        recon_button = ipyw.Button(description="Reconstruct", layout=self.button_layout)
        self.widgets = [explanation, self.img_disp, recon_button]
        self.panel = ipyw.VBox(children=self.widgets, layout=self.panel_layout)
        recon_button.on_click(self.nextStep)

    def nextStep(self):
        xmin = self.img_disp._xcoord_absolute
        ymin = self.img_disp._ycoord_absolute
        xmax = self.img_disp._xcoord_max_roi
        ymax = self.img_disp._ycoord_max_roi
        self.ct.recon(crop_window=(xmin, ymin, xmax, ymax), remove_rings_at_sinograms=self.remove_rings, smooth_recon=self.smooth_recon, smooth_projection=self.smooth_projection)       
        print self.config.workdir
