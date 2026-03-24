import pymd.MD.recipies.standard_md as standard_md
import pymd.tools.io as io
from pymd.MD.md import MDClass

from pprint import pprint
import pytest
import pytest_subprocess.fake_process as fake_process
import os

temp_dir = "./test/temp_dir"

commands = ["sander -O -i min1.in -c start.rst7 -r complex.parm7 -o min1.out -r min1.rst7 -x min1.nc"]

def test_initialisation(fp):
    io.make_dir(temp_dir)
    io.text_dump("", os.path.join(temp_dir, "start.rst7") )
    io.text_dump("", os.path.join(temp_dir, "complex.parm7") )
    fp.register(command=commands, stdout="This command was run", )
    MM = MDClass("AMBER")
    MM.set_parmfile("complex.parm7")
    MM.define_hardware(cpu=12)

    MM = standard_md.initialise_system(MM, path=temp_dir)

    pprint(vars(MM))
    pprint((MM.jobs[0].kernel.config.to_dict()))
    pprint((MM.jobs[1].kernel.config.to_dict()))
    assert len(MM.jobs) == 5
    for job in MM.jobs:
        assert job.complete == False # Jobs should not have been run
        job.exe()
    # assert False