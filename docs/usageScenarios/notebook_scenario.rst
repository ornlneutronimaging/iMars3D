Data used: IPTS-25777

* Raw projections:   /HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man/*
* ob: /HFIR/CG1D/IPTS-25777/raw/ob/Oct29_2019/*
* df: /HFIR/CG1D/IPTS-25777/raw/df/Oct29_2019/*

Notebook to use on jupyter.sns.gov: ~/notebooks/CG1DImaging/TomoRecon-UI_v2.ipynb
Kernel to use: N/A

Run cells from top


then run following cell

.. image:: ../_static/image01.png

Click Start from scratch

.. image:: /_static/image02.png

Select CG1D and click OK

.. image:: /_static/image03.png

Enter 25777 and click OK

.. image:: /_static/image04.png

Enter iron_man and click OK

.. image:: /_static/image05.png

Keep the same default value and just click OK

.. image:: /_static/image06.png

Same thing, keep the same default value and click OK

.. image:: /_static/image07.png

Keep the selected folder (iron_man) and click Select

.. image:: /_static/image08.png

The notebook will list a few of the data file found to show that it found the data. Click OK

.. image:: /_static/image09.png

We now need to select the OB (Open Beam) to use.
Navigate to the folder raw/ob/Oct29_2019 and select all the files listed + click Select

If you need need in using the file dialog provided (ipywe library), refer to the following tutorial (https://neutronimaging.pages.ornl.gov/tutorial/notebooks/file_selector)

.. image:: /_static/image10.gif

Repeat with the DF found in raw/df/Oct29_2019/ and select all the files listed and click Select

.. image:: /_static/image11.png

The notebook will then start to run a few methods (averaging dark field, averaging open beam, normalization, gamma filtering). Just be patient and wait until you see a preview of the data to reconstruct.

.. image:: /_static/image12.png

.. image:: /_static/image13.png

Use the right vertical slider to improve the contrast and be able to see the sample (Be patient with the slider).
Using the mouse (continuous left click), select a box inside the field of view.

.. image:: /_static/image14.png

And click Zoom to validate your selection and crop the image.

.. image:: /_static/image15.png

Then click Reconstruct to launch the reconstruction algorithm.

.. image:: /_static/image16.png

This take around 1 or 2 minutes.

.. image:: /_static/image17.png

The reconstruction is done when you see the following message at the bottom of the cell.

.. image:: /_static/image18.gif

To visualize the reconstructed data, go to the analysis.sns.gov server. Using the file dialog, navigate to
/HFIR/CG1D/IPTS-25777/shared/processed_data/iron_man

Start the Fiji (ImageJ) application by clicking   Applications > Analysis > ImageJ
Then click the Iron_man folder and move it into the ImageJ status bar to load the data (make sure you select use virtual stack)
