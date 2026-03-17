import pyMD.MD.recipies.standard_MD as standard_MD
from pyMD.MD.MD import MDClass

from pprint import pprint

def test_initialisation():
    MM = MDClass("AMBER")
    MM.set_parmfile("complex.parm7")
    MM.define_Hardware(CPU=12)

    MM = standard_MD.initialise_system(MM)

    pprint(vars(MM))
    pprint((MM.jobs[0].kernel.config.to_dict()))
    pprint((MM.jobs[1].kernel.config.to_dict()))
    assert len(MM.jobs) == 3
    for job in MM.jobs:
        assert job.complete == False
    # assert False