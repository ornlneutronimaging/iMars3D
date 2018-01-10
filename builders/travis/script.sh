#!/bin/bash

set -e

source activate testenv
python builders/setup-aws-testconfig.py
python tests/getdata.py
python tests/imars3d/signon.py

if [ ${TRAVIS_EVENT_TYPE} == "cron" ]; then
    travis_wait 60 python tests/workflows/recon/test_CT_travisCI.py test
    travis_wait 60 python tests/workflows/recon/test_CT_travisCI.py test2
else
    py.test
fi

