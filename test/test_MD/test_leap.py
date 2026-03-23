import pyMD.tools.io as io
import pyMD.MD.utilities.parameterise as parameterise

import subprocess


test_pdb = "1N23"
test_pdb_location = "https://files.rcsb.org/download/1N23.pdb"
temp_dir = "./test/temp_dir"


def test_tleap():
    io.MakeDir(temp_dir)
    subprocess.run(["wget", test_pdb_location], cwd=temp_dir)
    # parameterise.gen_leap()