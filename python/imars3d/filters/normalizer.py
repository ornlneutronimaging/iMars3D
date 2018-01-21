# -*- python -*-
# -*- coding: utf-8 -*-

from __future__ import print_function
import progressbar, numpy as np, os

def average(image_collection):
    N = image_collection.nImages
    assert N, "image_collection %s does contain any images" % (image_collection.name,)
    res = None
    prefix = "Averaging %s:" % image_collection.name or ""
    bar = progressbar.ProgressBar(
        widgets=[
            prefix,
            progressbar.Percentage(),
            progressbar.Bar(),
            ' [', progressbar.ETA(), '] ',
        ],
        max_value = N-1
    )
    for i, im in enumerate(image_collection.iterImages()):
        data = np.array(im.getData(), dtype="float32")
        if res is None:
            res = data
        else:
            res += data
        bar.update(i)
        continue
    print()
    return res/N


def normalize(ct_series, df_images, ob_images, workdir, output_img_series):
    """
    * ct_series: an image series for ct scan
    * df_images: dark field image collection. can be None
    * ob_images: open beam image collection
    * workdir: path where intermediate data files will be written into
    """
    # compute dark field and open beam
    if not os.path.exists(workdir):
        os.makedirs(workdir)
    # dark field
    if df_images is not None:
        df_output = os.path.join(workdir, "df.npy")
        if not os.path.exists(df_output):
            df = average(df_images)
            np.save(df_output, df)
        else:
            df = np.load(df_output)
    else:
        df = 0.
    # open beam
    ob_output = os.path.join(workdir, "ob.npy")
    if not os.path.exists(ob_output):
        ob = average(ob_images)
        np.save(ob_output, ob)
    else:
        ob = np.load(ob_output)
    # normalize
    prefix = "Normalizing %s:" % ct_series.name or ""
    N = ct_series.nImages
    bar = progressbar.ProgressBar(
        widgets=[
            prefix,
            progressbar.Percentage(),
            progressbar.Bar(),
            ' [', progressbar.ETA(), '] ',
        ],
        max_value = N-1
    )
    for i, angle in enumerate(ct_series.identifiers):
        # skip over existing results
        if not output_img_series.exists(angle):
            data = np.array(ct_series.getData(angle), dtype="float32")
            data = (data-df)/ob
            output_img_series.putImage(angle, data)
        bar.update(i)
        continue
    print('\n')
    return

# End of file
