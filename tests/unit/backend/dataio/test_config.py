#!/usr/bin/env python3
import pytest
import os
import json
from imars3d.backend.dataio.config import save_config


def test_save_config():
    config = {"test": 1}
    # error_1: incorrect file extension
    with pytest.raises(ValueError):
        save_config(config, "test.test")
    # case: save correctly
    filepath = "test.json"
    save_config(config, filepath)
    with open(filepath, "r") as infile:
        config_readin = json.load(infile)
    assert config == config_readin
    # cleanup
    os.remove(filepath)


if __name__ == "__main__":
    pytest.main([__file__])
