import os
from pprint import pprint

from pymd.tools.status_tracker import StatusTracker
from pymd.tools import io

TEMP_DIR = "./test/temp_dir"

def test_status_tracker() -> None:
    io.make_dir(TEMP_DIR)
    assert os.path.isfile(os.path.join(TEMP_DIR, "STATUS.json")) is False

    TEST_STAGES: list[str] = ["setup", "equilibration", "mutation"]
    TEST_STEPS: list[str] = ["min", "heat", "equil",]
    
    status = StatusTracker(stages=TEST_STAGES, file_path=os.path.join(TEMP_DIR, "STATUS.json"))
    status.add_steps(stage="setup", steps=TEST_STEPS)
    status.update_step(stage="setup", step="min", status="Running")
    io.remove_dir(TEMP_DIR, force=True)

    
