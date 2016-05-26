# -*- python -*-
# -*- coding: utf-8 -*-


def filter(ct_series, output_img_series, **kwds):
    """
    * ct_series: an image series for ct scan
    """
    prefix = "Cropping %s:" % ct_series.name or ""
    N = ct_series.nImages
    import progressbar
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
            data = ct_series.getData(angle)
            output_img_series.putImage(angle, filter_one(data, **kwds))
        bar.update(i)
        continue
    print
    return


def filter_one(img, box=None):
    """cropping given image
    - img: image npy array
    - box: box of cropping
    """
    left, right, top, bottom = box
    img = img[top:bottom+1, left:right+1]
    return img

