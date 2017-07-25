# coding: utf-8

import os, subprocess, numpy as np
import ipywidgets as ipyw
import pickle as pkl
from ipywe import ImageDisplay, ImageSlider
from .ct_wizard import ct_wizard as ctw
from IPython.display import display, HTML, clear_output

class ReconPanel:

    panel_layout = ipyw.Layout(border="1px lightgray solid", margin="5px", padding="15px")
    button_layout = ipyw.Layout(margin="10px 5px 5px 5px")

    def show(self):
        display(self.panel)

    def remove(self):
        for w in self.widgets: w.close()
        self.panel.close()

    def nextStep(self):
        raise NotImplementedError

class ReconStartButtons(ReconPanel):
    
    def __init__(self, image_width=300, image_height=300, remove_rings_at_sinograms=False, smooth_recon=False):
        self.img_width = image_width
        self.img_height = image_height
        self.remove_rings = remove_rings_at_sinograms
        self.smooth_recon = smooth_recon
        self.label_layout = ipyw.Layout(height='35px', padding='8px', width='300px')
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
        self.remove()
        wizard_panel = ReconWizard(self.img_width, self.img_height, self.remove_rings, self.smooth_recon)
        wizard_panel.show()
        return

    def reloadConfig(self):
        config = pkl.load(open('/HFIR/CG1D/IPTS-15518/shared/processed_data/derek_inj/recon-config.pkl'))
        subprocess.call(["mkdir", config.outdir])
        os.chdir(config.outdir)
        assert os.getcwd() == config.outdir
        pkl.dump(config, open('recon-config.pkl', 'wb'))
        for k, v in config.__dict__.items():
            if k.startswith('_'): continue
            sv = str(v)
            if len(sv) > 60:
                sv = sv[:50] + '...'
            print "{0:20}{1:<}".format(k,sv)
        self.remove()
        ct_create = CTCreationPanel(self.img_width, self.img_height, self.remove_rings, self.smooth_recon, config)
        ct_create.show()
        return
        
class ReconWizard(ReconPanel):

    def __init__(self, image_width, image_height, remove_rings_at_sinograms, smooth_recon):
        self.img_width = image_width
        self.img_height = image_height
        self.remove_rings = remove_rings_at_sinograms
        self.smooth_recon = smooth_recon
        self.config = None
        self.createWizardPanel()
        return

    def createWizardPanel(self):
        self.config = ctw.config()
        ctw.wizard(self.config)
        self.saveConfig()
        return

    def saveConfig(self):
        subprocess.call(["mkdir", self.config.outdir])
        os.chdir(config.outdir)
        assert os.getcwd() == self.config.outdir
        pkl.dump(config, open('recon-config.pkl', 'wb'))
        for k, v in self.config.__dict__.items():
            if k.startswith('_'): continue
            sv = str(v)
            if len(sv) > 60:
                sv = sv[:50] + '...'
            print "{0:20}{1:<}".format(k,sv)
        self.nextStep()

    def nextStep(self):
        self.remove()
        ct_create = CTCreationPanel(self.img_width, self.img_height, self.remove_rings, self.smooth_recon, self.config)
        ct_create.show()
        return

class CTCreationPanel(ReconPanel):

    def __init__(self, image_width, image_height, remove_rings_at_sinograms, smooth_recon, config):
        self.img_width = image_width
        self.img_height = image_height
        self.remove_rings = remove_rings_at_sinograms
        self.smooth_recon = smooth_recon
        self.config = config
        self.ct = None
        self.ppd = None
        self.createCT()
        return

    def createCT(self):
        from imars3d.CT import CT
        self.ct = CT(self.config.datadir, CT_subdir=self.config.ct_dir, CT_identifier=self.config.ct_sig, workdir=self.config.workdir, outdir=self.config.outdir, ob_files=self.config.ob_files, df_files=self.config.df_files) #ob_identifier=ob_sig, df_identifier=df_sig
        #Ignoring the %%time magics for now
        self.ppd = self.ct.preprocess()
        self.nextStep()

    def nextStep(self)
        self.remove()
        slider_roi = ImgSliderROIPanel(self.img_width, self.img_height, self.remove_rings, self.smooth_recon, self.config, self.ct, self.ppd)
        slider_roi.show()

class ImgSliderROIPanel(ReconPanel):

    def __init__(self, image_width, image_height, remove_rings_at_sinograms, smooth_recon, config, ct, ppd):
        self.img_width = image_width
        self.img_height = image_height
        self.remove_rings = remove_rings_at_sinograms
        self.smooth_recon = smooth_recon
        self.config = config
        self.ct = ct
        self.ppd = ppd
        self.createTabs()

    def createTabs():
        
