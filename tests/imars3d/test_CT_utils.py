#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, numpy as np, shutil, glob
here = os.path.dirname(__file__)


def test():
    src = '_tmp.archive.src'
    if os.path.exists(src): 
        if os.path.islink(src): os.unlink(src)
        else: shutil.rmtree(src)
    os.makedirs(src)
    open(os.path.join(src, 'a.txt'), 'wt').write('')
    from imars3d.CTProcessor import archive_bg
    dest = '_tmp.archive.dest'
    if os.path.exists(dest): shutil.rmtree(dest)
    os.makedirs(dest)
    archive_bg(src, dest)
    import time; time.sleep(10)
    dest1 = glob.glob(os.path.join(dest, 'work*'))[0]
    assert os.path.exists(os.path.join(dest1, 'a.txt'))
    return


def main():
    test()
    return


if __name__ == '__main__': main()
