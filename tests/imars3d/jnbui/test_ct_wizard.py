#!/usr/bin/env python

import pytest
from imars3d.jnbui import ct_wizard
import os

here = os.path.abspath(os.path.dirname(__file__))


def test_wizard():
    config = ct_wizard.config()
    ct_wizard.wizard(config)
    return


def test_load():
    import pickle as pkl
    config = pkl.load(open(os.path.join(here, 'recon-config.pkl')))
    assert config.df_dir == '/HFIR/CG1D/IPTS-15518/raw/df'
    assert config.ct_subdir == 'Derek_injec'
    assert config.ct_dir == '/HFIR/CG1D/IPTS-15518/raw/ct_scans/Derek_injec'
    assert config.ob_dir == '/HFIR/CG1D/IPTS-15518/raw/ob'
    assert config.workdir == '/SNSlocal2/lj7/derek_inj'
    assert config.outdir == '/HFIR/CG1D/IPTS-15518/shared/processed_data/derek_inj'
    return

def main():
    test_wizard()
    test_load()
    return


if __name__ == "__main__":
    pytest.main([__file__])
