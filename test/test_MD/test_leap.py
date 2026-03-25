import pymd.tools.io as io
import pymd.md.utilities.antechamber as antechamber

import subprocess


test_pdb = "1N23"
test_pdb_location = "https://files.rcsb.org/download/1N23.pdb"
temp_dir = "./test/temp_dir"


def test_tleap():
    io.make_dir(temp_dir)
    subprocess.run(["wget", test_pdb_location], cwd=temp_dir)
    io.remove_dir(temp_dir, force=True)
    # parameterise.gen_leap()