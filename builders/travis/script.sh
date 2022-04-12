#P!/bin/bash

set -e

source activate testenv
export PYTHONPATH=$PWD/python

python builders/setup-aws-testconfig.py
python tests/getdata.py
python tests/imars3d/signon.py

if [ ${TRAVIS_EVENT_TYPE} == "cron" ]; then
    echo "* Running CT workflow tests"
    python tests/workflows/recon/test_CT_travisCI.py test
    # rm -rf work out
    # python tests/workflows/recon/test_CT_travisCI.py test2
    echo "  - Done."
else
    echo "* Running unittests"
    py.test
    # py.test tests/imars3d/recon/test_mpi.py
    echo "  - Done."
fi
