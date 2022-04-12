#!/usr/bin/env python

from imars3d.jnbui import ct_wizard
import os

here = os.path.abspath(os.path.dirname(__file__))


def test_wizard():
    config = ct_wizard.config()
    ct_wizard.wizard(config)
    return


def skip_test_load():
    # TODO FIXME - Jean: disable now.  In future a python 3.6 pickle file will be generated for python 3.6 test.
    import pickle as pkl

    print("[DEBUG] Here: {}".format(here))
    test_pkl_file = os.path.join(here, "recon-config.pkl")
    print("[DEBUG] Pickle file: {}".format(test_pkl_file))
    config_file = open(os.path.join(here, "recon-config.pkl"), "rb")
    print("[DEBUG] config file type: {}".format(type(config_file)))
    config = pkl.load(config_file, encoding="bytes")
    assert config.df_dir == "/HFIR/CG1D/IPTS-15518/raw/df"
    assert config.ct_subdir == "Derek_injec"
    assert config.ct_dir == "/HFIR/CG1D/IPTS-15518/raw/ct_scans/Derek_injec"
    assert config.ob_dir == "/HFIR/CG1D/IPTS-15518/raw/ob"
    assert config.workdir == "/SNSlocal2/lj7/derek_inj"
    assert config.outdir == "/HFIR/CG1D/IPTS-15518/shared/processed_data/derek_inj"
    config_file.close()


def main():
    test_wizard()
    test_load()
    return


if __name__ == "__main__":
    main()
