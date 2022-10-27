# backend module integration tests

# create json test data
import json

from imars3d.backend.workflow.engine import WorkflowEngineAuto
import pytest


@pytest.fixture(scope="module")
def config():
    config_str = """
{
    "facility": "HFIR",
    "instrument": "CG1D",
    "ipts": "IPTS-1234",
    "name": "name for reconstructed ct scans",
    "workingdir": "/path/to/working/dir",
    "outputdir": "/path/to/output/dir",
    "tasks": [{
    "name": "task1",
    "function": "imars3d.backend.io.data.load_data",
    "inputs": {
    "ct_dir": "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man",
    "ob_dir": "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ob/Oct29_2019/",
    "dc_dir": "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/df/Oct29_2019/",
    "ct_fnmatch": "*.tiff",
    "ob_fnmatch": "*.tiff",
    "dc_fnmatch": "*.tiff"
    },
    "outputs": ["ct", "ob", "dc", "rot_angles"]
    }
    ]
}"""
    return json.loads(config_str)


class TestWorkflowEngineAuto:
    def test_config(self, config):
        workflow = WorkflowEngineAuto(config)
        workflow.run()