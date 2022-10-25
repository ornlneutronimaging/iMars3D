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


@pytest.fixture(scope="module")
def config():
    config_str = """{
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
				"ct_dir": "/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man",
				"ob_dir": "/HFIR/CG1D/IPTS-25777/raw/ob/Oct29_2019/",
				"dc_dir": "/HFIR/CG1D/IPTS-25777/raw/df/Oct29_2019/",
				"ct_fnmatch": "*.tiff",
				"ob_fnmatch": "*.tiff",
				"dc_fnmatch": "*.tiff"
			},
			"outputs": ["ct", "ob", "dc", "rot_angles"]
		},
		{
			"name": "task2",
			"function": "imars3d.backend.morph.crop.crop",
			"inputs": {
                "ct": "ct",
				"crop_limit": [552, 1494, 771, 1296]
			},
			"outputs": ["ct", "ob", "dc"]
		},
		{
			"name": "task3",
			"function": "imars3d.backend.corrections.gamma_filter.gamma_filter",
			"inputs": {
				"rot_center": "0.0"
			},
			"outputs": ["ct"]
		},
		{
			"name": "task4",
			"function": "imars3d.backend.preparation.normalization.normalization",
			"inputs": {
				"arrays": "ct",
				"flats": "ob",
				"darks": "dc"
			},
			"outputs": ["ct"]
		},
		{
			"name": "task5",
			"function": "imars3d.backend.corrections.denoise.denoise",
			"inputs": {
				"arrays": "ct"
			},
			"outputs": ["ct"]
		},
		{
			"name": "task6",
			"function": "imars3d.backend.corrections.ring_removal.remove_ring_artifact",
			"inputs": {
				"arrays": "ct"
			},
			"outputs": ["ct"]
		},
		{
			"name": "task7",
			"function": "imars3d.backend.diagnostics.rotation.find_rotation_center",
			"inputs": {
				"arrays": "ct",
				"angles": "rot_angles",
				"in_degrees": true,
				"atol_deg": 0.5
			},
			"outputs": ["ct"]
		},
		{
			"name": "task8",
			"function": "imars3d.backend.reconstruction.recon",
			"inputs": {
				"arrays": "ct",
				"theta": "rot_angles",
				"center": "rot_cnt"
			},
			"outputs": ["ct"]
		}
	]
}"""
    return json.loads(config_str)

class TestWorkflowEngineAuto:
    def test_config(self, config):
        workflow = WorkflowEngineAuto(config)
        workflow.run()
        assert workflow.config == config

    def test_run(self, config):
        workflow = WorkflowEngineAuto(config)
        workflow.run()
        assert workflow.tasks[0].outputs["ct"] == ["ct1", "ct2", "ct3"]
        assert workflow.tasks[1].outputs["ct"] == ["ct1", "ct2", "ct3"]
        assert workflow.tasks[2].outputs["ct"] == ["ct1", "ct2", "ct3"]

