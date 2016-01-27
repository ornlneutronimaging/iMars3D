# ivenus.tilt

def check(tilt, img0, img180):
    """check tilt using a pair of images
    """
    from scipy import ndimage
    import numpy as np
    
    data0 = img0.getData()
    data0 = ndimage.rotate(data0, -tilt)
    
    data180 = img180.getData()
    data180 = ndimage.rotate(data180, -tilt)
    data180 = np.fliplr(data180)
    
    from ivenus import io
    out = io.ImageFile("tilted-0.npy")
    out.data = data0; out.save()
    
    out = io.ImageFile("tilted-180.npy")
    out.data = data180; out.save()
    return
