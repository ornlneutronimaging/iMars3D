#!/usr/bin/env python

root = "recon"
out = "recon-gathered"
node_prefix = "node"
step_prefix = "step"
img_prefix = "recon_"
start_layer = 150
step_size = 10
steps = 5

import glob, os, sys

if not os.path.exists(out):
    os.makedirs(out)
    
for nodedir in glob.glob(os.path.join(root, "%s*" % node_prefix)):
    node = int(os.path.basename(nodedir).lstrip(node_prefix))
    for stepdir in glob.glob(os.path.join(nodedir, "%s*" % step_prefix)):
        step = int(os.path.basename(stepdir).lstrip(step_prefix))
        print node, step
        for img in glob.glob(os.path.join(stepdir, "%s*" % img_prefix)):
            index = os.path.splitext(os.path.basename(img))[0].lstrip(img_prefix)
            index = int(index)
            layer = node*step_size*steps + step*step_size + index + start_layer
            newname = os.path.join(out, "layer_%05i.tiff" % layer)
            print "%s --> %s" % (img, newname)
            os.rename(img, newname)
        continue
