#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tomopy
from ivenus.io import ImageSeries

ob_data = []
for _file in list_ob_files:
    ob_data.append(pyfits.open(_file)[0].data)
    type(pyfits.open(_file))


df_data = []
for _file in list_df_files:
    df_data.append(pyfits.open(_file)[0].data)

data = []
for _file in list_data_files:
    data.append(pyfits.open(_file)[0].data)


proj = tomopy.normalize(data, ob_data, df_data)
step = 0.85
theta = np.pi/180.*(np.arange(0.0, 181.9+step, step))
rot_center = tomopy.find_center(
    proj, theta, emission=False, init=1024, tol=0.5)
print("Center of rotation: ", rot_center)

tomopy.write_center(proj.copy(), theta, dpath='tmp', emission=False)
print proj.shape
rot_center = tomopy.find_center_vo(proj.copy())
print("Center of rotation: ", rot_center)

proj = tomopy.normalize_bg(data)

fig, ax = plt.subplots()
im = plt.imshow(data[0], cmap='gray') #, vmin=0.2, vmax=1.2
fig.colorbar(im)


fig, ax = plt.subplots()
im = plt.imshow(proj[:, 1000, :], cmap='gray')
fig.colorbar(im)


tomopy.write_tiff_stack(proj, fname='sino-tmp', axis=1, overwrite=True)

rec = tomopy.recon(
    proj[:, 600:601, :], theta=theta, center=1023.2,
    algorithm='gridrec', emission=False)

fig, ax = plt.subplots()
im = plt.imshow(rec[0], cmap='gray')
fig.colorbar(im)

print proj.shape, rec.shape
tomopy.write_tiff_stack(rec, fname='reco-tmp', axis=0, overwrite=True)
