For this scenario, as soon as a full set of 3D acquisition is done (when all the rotation angle have been acquired)
iMars3D should be automatically triggered and reconstruct the data and export them into the IPTS-XXXX/shared/processed_data folder.

This scenario used to work and stopped working 2 years ago. Script used can be find in `/HFIR/CG1D/shared/autoreduce`

This script took 2 arguments

* input folder
* output folder

To test this work, the following folders can be used

* input folder -> /HFIR/CG1D/IPTS-25777/raw/ct-scans/iron_man
* output folder -> /HFIR/CG1D/IPTS-25777/shared/processed_data/
