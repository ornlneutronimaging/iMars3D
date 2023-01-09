#!/usr/bin/env python3
import pytest
import time
from panel.widgets import Tqdm
from tqdm.contrib.concurrent import process_map


def test_progress_bar_panel():
    tqdm_obj = Tqdm()
    # make sure the bar starts at zero
    assert tqdm_obj.value == 0

    NUM_ITEMS = 10
    # run process map to sleep .3 seconds for each of ten items
    _ = process_map(time.sleep, [0.3] * NUM_ITEMS, max_workers=2, tqdm_class=tqdm_obj)
    # make sure the bar finishes where it should
    assert tqdm_obj.value == NUM_ITEMS


if __name__ == "__main__":
    pytest.main([__file__])
