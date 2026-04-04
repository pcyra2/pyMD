from pprint import pprint
import os
import numpy

import pymd.tools.structure as structure
from pymd.qm.kernels.orca import Orca
from pymd.tools import io

TEMP_DIR = "./test/temp_dir"

H2 = f"""2

H 0 0 0
H 1.2 0 0"""

def test_h2_single_point() -> None:
    io.make_dir(path=TEMP_DIR)
    TEST_MOL = structure.Molecule()
    TEST_MOL.from_xyz(lines=H2, charge=0, spin=0)

    orca = Orca(input_file_name="Orca.inp", output_file_name="Orca.out", coordinates=TEST_MOL)
    orca.set_run_path(path=TEMP_DIR)
    orca.set_standard_variables(method = "PBE", basis = "6-31+G*", disp="D3BJ")
    orca.run()

    assert numpy.isclose(a=orca._energies[0], b=-1.104124817274)
    assert len(orca._energies) == 1
    io.remove_dir(path=TEMP_DIR, force=True)

