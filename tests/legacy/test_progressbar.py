#!/usr/bin/env python

import time
import progressbar


def test():
    bar = progressbar.ProgressBar(widgets=[
        progressbar.Percentage(),
        ' [', progressbar.Timer(), '] ',
        progressbar.Bar(),
        ' (', progressbar.ETA(), ') ',
        ])
    for i in bar(range(10)):
        time.sleep(0.1)
    return

if __name__ == '__main__': test()
