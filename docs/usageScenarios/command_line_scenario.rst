Data used: IPTS-25777

* Raw projections:   /HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man/*
* ob: /HFIR/CG1D/IPTS-25777/raw/ob/Oct29_2019/*
* df: /HFIR/CG1D/IPTS-25777/raw/df/Oct29_2019/*

iMars3D should be available to the user as a conda or pip application and be executed using a simple command line
that may look like

```
iMars3d --raw-projections /HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man/* --ob /HFIR/CG1D/IPTS-25777/raw/ob/Oct29_2019/*
--df /HFIR/CG1D/IPTS-25777/raw/df/Oct29_2019/* --tilt-correction 0.01 --crop-x0 10 --crop-y0 20 --crop-x1 500 --crop-y1 390
```



