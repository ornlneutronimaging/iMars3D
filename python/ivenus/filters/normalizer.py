# -*- python -*-
# -*- coding: utf-8 -*-


def average(image_collection, prefix, console_out):
    N = image_collection.nImages
    assert N
    res = None
    for i, im in enumerate(image_collection.iterImages()):
        data = np.array(im.getData(), dtype=float)
        if res is None:
            res = data
        else:
            res += data
        console_out.write("\r%s: %2.0f%%" % (prefix, (i+1)*100./N))
        console_out.flush()
        continue
    return res/N


def normalize(ct_series, df_images, ob_images, output_template, console_out):
    # compute dark field and open beam
    df_output = "df.npy"
    if not os.path.exists(df_output):
        df = average(df_images, "Dark field:", console_out)
        console_out.write("\n")
        np.save(df_output, df)
    else:
        df = np.load(df_output)
    ob_output = "ob.npy"
    if not os.path.exists(ob_output):
        ob = average(ob_images, "Open beam:", console_out)
        console_out.write("\n")
        np.save(ob_output, ob)
    else:
        ob = np.load(ob_output)
    # normalize
    prefix = "Normalize:"
    N = len(ct_series.identifiers)
    for i, angle in enumerate(ct_series.identifiers):
        fn = output_template % angle
        # skip over existing results
        if os.path.exists(fn): continue
        data = np.array(ct_series.getData(angle), dtype=float)
        data = (data-df)/ob
        f = ImageFile(fn)
        f.data = data
        f.save()
        console_out.write("\r%s: %2.0f%%" % (prefix, (i+1)*100./N))
        console_out.flush()
        continue
    console_out.write("\n")
    return

# End of file
