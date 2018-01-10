#!/bin/bash

set -e

source activate testenv
python builders/setup-aws-testconfig.py
python tests/getdata.py
python tests/imars3d/signon.py
py.test
# rm -rf work out tests/imars3d    # clean up to have enough space for the next test
# travis_wait 60 python tests/workflows/recon/test_CT_travisCI.py
