# -*- python -*-
# -*- coding: utf-8 -*-


def filter(ct_series, output_img_series, **kwds):
    """
    * ct_series: an image series for ct scan
    """
    prefix = "Smoothing %s:" % ct_series.name or ""
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


def filter_one(img, size):
    """smoothing given image
    - img: image npy array
    - size: size of median filter
    """
    from scipy.ndimage import median_filter
    return median_filter(img, size)

