import glob
import os
from pymd.tools import io
from pymd.user_configs.hpc_defaults import DEFAULT_HPC
from pymd.tools import slurm

ADA_TEST_DIR = "~/pyMD_Test"
FILE_LOC = "./test/test_data/"
TEST_DIR =  "./test/temp_dir/"


def test_default_hpc():
    DEFAULT_HPC.make_dir(ADA_TEST_DIR)
    DEFAULT_HPC.sync(FILE_LOC, ADA_TEST_DIR, "forward")
    io.make_dir(TEST_DIR)
    DEFAULT_HPC.sync(TEST_DIR, ADA_TEST_DIR, "backward")
    correct_files = [file.split("/")[-1] for file in glob.glob(f"{FILE_LOC}*")]
    test_files = [file.split("/")[-1] for file in glob.glob(f"{TEST_DIR}*")]
    assert correct_files == test_files
    DEFAULT_HPC.remove_dir(ADA_TEST_DIR)
    io.remove_dir(TEST_DIR, force=True)

def test_submission():
    sub = slurm.Slurm()
    sub.set_name("pytest")
    sub.set_mem(1)
    sub.set_gpus(0)
    sub.set_ntasks(1)
    sub_script = sub.gen_script("sleep 120")
    sub.define_dirs(TEST_DIR, ADA_TEST_DIR)
    io.make_dir(TEST_DIR)
    io.text_dump(sub_script, os.path.join(TEST_DIR,"sub.sh"))
    sub.hpc.make_dir(ADA_TEST_DIR)
    sub.submit(wait_for_finish=True)
    sub.hpc.sync(TEST_DIR, ADA_TEST_DIR, "backward")
    assert os.path.isfile(os.path.join(TEST_DIR, f"slurm-{sub.job.job_id}.out"))
    sub.hpc.remove_dir(ADA_TEST_DIR)
    io.remove_dir(TEST_DIR, True)
