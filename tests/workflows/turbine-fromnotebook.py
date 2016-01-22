# coding: utf-8

import tomopy, pyfits, numpy as np, os, glob
import matplotlib.pyplot as plt, pylab

datadir = "/home/lj7/imaging/2nd-try/turbine"

# load the OB
ob_folder = os.path.join(datadir, "ob")
list_ob_files = glob.glob(ob_folder + '/*')
number_of_ob = len(list_ob_files)
print(number_of_ob)
# data
ob_data = []
for _file in list_ob_files:
    ob_data.append(pyfits.open(_file)[0].data)
print type(ob_data[0])
print ob_data[1]
print ob_data[0].shape


# load the DF
df_folder = os.path.join(datadir, "df")
list_df_files = glob.glob(df_folder + '/*')
df_data = []
for _file in list_df_files:
    df_data.append(pyfits.open(_file)[0].data)


# load the data
data_folder = os.path.join(datadir, "ct")
# 
def getFilename(filename_template, angle):
    path_pattern = filename_template % (angle,)
    dir = os.path.dirname(path_pattern)
    basename = os.path.basename(path_pattern)
    base, ext = os.path.splitext(basename)
    # bad code
    path_pattern = os.path.join(dir, base.replace(".", "[_.]") + ext)
    
    paths = glob.glob(path_pattern)
    if len(paths)!=1:
        raise RuntimeError, "template %r no good: \npath_pattern=%r" % (
            filename_template, path_pattern)
    
    path = paths[0]
    return path
# test
angle=0; print getFilename(data_folder+"/2012*_%.3f_*.fits", angle)
#
step = 0.85
angles=np.arange(0.0, 181.9+step, step);
list_data_files = map(lambda x: getFilename(data_folder+"/2012*_%.3f_*.fits", x), angles);
data = []
for _file in list_data_files:
    data.append(pyfits.open(_file)[0].data)

# now start processing
# normalize
print "* normalizing ..."
proj = tomopy.normalize(data, ob_data, df_data)
print "  done."
# checking
print proj.shape
theta = np.arange(0.0, 181.9+step, step)
print(theta)
theta *= np.pi/180.
# calculate rotation center
print "* finding center ..."
rot_center = tomopy.find_center(proj, theta, emission=False, init=1024, tol=0.5)
print "  done."
print("Center of rotation: ", rot_center)
# checking
print proj.shape
tomopy.write_center(proj.copy(), theta, dpath='center', emission=False)
# rot_center = tomopy.find_center_vo(proj.copy())
# print("Center of rotation: ", rot_center)
# plot data
# print "* normalizing bg ..."
# proj = tomopy.normalize_bg(data)
# print "  done."

# plot an image
fig, ax = plt.subplots()
im = plt.imshow(data[0], cmap='gray') #, vmin=0.2, vmax=1.2
fig.colorbar(im)
# plot a projection
fig, ax = plt.subplots()
im = plt.imshow(proj[:, 1000, :], cmap='gray')
fig.colorbar(im)
# dump
# tomopy.write_tiff_stack(proj, fname='proj', axis=1, overwrite=True)
# reconstruction
print "* reconstructing ..."
rec = tomopy.recon(
    # proj[:, 600:601, :], 
    proj[:, 1023:1024, :], 
    theta=theta, center=rot_center[0], 
    algorithm='gridrec', emission=False
)
print "  done."
# plot
fig, ax = plt.subplots()
im = plt.imshow(rec[0], cmap='gray')
fig.colorbar(im)
pylab.show()
print proj.shape, rec.shape
# dump
tomopy.write_tiff_stack(rec, fname='recon', axis=0, overwrite=True)

