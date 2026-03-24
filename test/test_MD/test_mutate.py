import pymd.MD.utilities.mutate as mutate 
import pymd.tools.io as io

import os

file_loc = "./test/test_data/"


def test_mutate():
    original_pdb = io.text_read(os.path.join(file_loc, "1N23.pdb"))
    mutated_pdb = mutate.mutate_residue(original_pdb, 112, "MET")
    reference_mutant = io.text_read(os.path.join(file_loc, "1N23_mutated112-MET.pdb"))

    for i, line in enumerate(mutated_pdb):
        assert line == reference_mutant[i]

    assert mutated_pdb == reference_mutant
    assert mutated_pdb != original_pdb

