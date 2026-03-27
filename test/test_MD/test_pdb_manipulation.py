import pymd.tools.pdb as pdb 
import pymd.tools.io as io

import os

file_loc = "./test/test_data/"


def test_mutate() -> None:
    original_pdb = io.text_read(os.path.join(file_loc, "1N23.pdb"))
    mutated_pdb = pdb.mutate_residue(original_pdb, 112, "MET")
    reference_mutant = io.text_read(os.path.join(file_loc, "1N23_mutated112-MET.pdb"))

    for i, line in enumerate(mutated_pdb):
        assert line == reference_mutant[i]

    assert mutated_pdb == reference_mutant
    assert mutated_pdb != original_pdb

def test_get_reidues()->None:
    original_pdb = io.text_read(path=os.path.join(file_loc, "1N23.pdb"))
    id = pdb.get_protein_res_id_range(lines=original_pdb)
    assert id == 598
