from pprint import pprint
import os
import numpy

import pymd.tools.structure as structure
from pymd.qm.kernels.orca import Orca
from pymd.tools import io

TEMP_DIR = "./test/temp_dir"

H2 = """2

H 0 0 0
H 1.2 0 0"""


THIO_MICHEAL = """9

S -2.22288361 0.95088031 -0.20261594
H -2.15295111 -0.23400882 -0.81650227
C -0.21379097 1.49869544 -0.93500781
C 0.09133654 1.22912728 -2.27661682
H 0.32028504 0.93030338 -0.19219147
H -0.33208708 2.53532312 -0.66421218
C 0.57073485 -0.02385563 -2.67960627
H -0.28300596 1.87299014 -3.05153304
N 0.99748311 -1.05122757 -3.02702825"""

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



def test_thio_micheal_optimisation() -> None:
    io.make_dir(path=TEMP_DIR)
    TEST_MOL = structure.Molecule()
    TEST_MOL.from_xyz(lines=THIO_MICHEAL, charge=-1, spin=0)

    orca = Orca(input_file_name="Orca.inp", output_file_name="Orca.out", coordinates=TEST_MOL)
    orca.set_run_path(path=TEMP_DIR)
    orca.set_standard_variables(method = "CCSD(T)", basis = "cc-pVTZ", )
    orca.add_job_variables("OptTS")
    orca.run()
    orca.print_output()
    assert False
    assert numpy.isclose(a=orca._energies[-1], b=-567.6448706978)
    assert len(orca._energies) == 1
    io.remove_dir(path=TEMP_DIR, force=True)