"""
Contains a python interface to tleap. This predominantly generates input files but 
also dictates the correct water forcefields for a given global forcefield. 
"""

import subprocess
import os
import pymd.tools.io as io

KNOWN_FORCEFIELDS = dict(ff14SB = dict(phosaa = "phosaa14SB",
                                    water = "TIP3P",
                                    waterff = "leaprc.water.tip3p",
                                    waterfix = ""
                                    ),
                        ff19SB = dict(phosaa = "phosaa19SB",
                                    water = "OPC",
                                    waterff = "leaprc.water.opc",
                                    waterfix = ""
                                    ) # Potentially need the water fix
                                    )

def gen_leap(ligand_name:str,
            pdb_file:str,
            parm_file: str = "complex.parm7",
            amber_coor: str = "complex.rst7",
            forcefield: str = "ff14SB",
            box: float = 12.0
            ) -> str:
    """
    """
    assert forcefield in KNOWN_FORCEFIELDS.keys(), f"ERROR: Forcefield {forcefield} unknown"

    file = f"""source leaprc.protein.{forcefield}
source leaprc.{KNOWN_FORCEFIELDS[forcefield]["phosaa"]}
source {KNOWN_FORCEFIELDS[forcefield]["waterff"]}

lig = loadmol2 {ligand_name}.mol2
loadamberparams {ligand_name}.frcmod
check lig

prot = loadpdb {pdb_file}
check prot

{KNOWN_FORCEFIELDS[forcefield]["waterfix"]}

complex = combine {"{"} prot lig {"}"}
solvateOct complex {KNOWN_FORCEFIELDS[forcefield]["water"]}BOX {box}
addions complex Na+ 0
savepdb complex complex.pdb
saveamberparm complex {parm_file} {amber_coor}
quit"""
    return file

def run_leap(path: str, file: str = "leap.in") -> None:
    """
    Runs tleap on the leap.in file

    Args:
        path (str): location of the leap.in file
    """
    log = subprocess.run(args=["tleap", "-f", file], cwd = path,
                            text = True, capture_output = True, check=True)
    io.text_dump(text=log.stdout, path=os.path.join(path, "leap.log"))

def gen_leap_ti(
        ligand_name: str,
        protein_1: str,
        protein_2: str,
        complex_out: str = "complex",
        protein_out: str = "protein",
        forcefield: str = "ff14SB",
        box: float = 12.0,
        gaff: str|None = None) -> str:
    """Generates the TI leap file which generates the dual-protein leap file.

    Args:
        ligand_name (str): name of the ligand file. This should be the prefix of the mol2 and 
            frcmod files which should be the same. (e.g. ligand.mol2, ligand.frcmod)
        protein_1 (str): name of the first protein PDB file, excluding the file extension.
        protein_2 (str): name of the second protein PDB file, excluding the file extension.
        complex_out (str, optional): name of the complex.rst7 and complex.parm7 files.
            Defaults to 'complex'.
        protein_out (str, optional): name of the protein.rst7 and protein.parm7 files.
            Defaults to 'protein'.
        forcefield (str, optional): name of the forcefield to use. Defaults to 'ff14SB'.
        box (float, optional): size of the waterbox to use. 
        gaff (str|None, optional): whether to also use a gaff forcefield. if so, 
            name the gaff forcefield. Defaults to None.
    """
    assert forcefield in KNOWN_FORCEFIELDS.keys(), f"ERROR: Forcefield {forcefield} unknown"

    if gaff is None:
        gaff_str = ""
    else:
        gaff_str = f"source leaprc.{gaff}"

    file = f"""source leaprc.protein.{forcefield}
source leaprc.{KNOWN_FORCEFIELDS[forcefield]["phosaa"]}
source {KNOWN_FORCEFIELDS[forcefield]["waterff"]}
{gaff_str}

lig = loadmol2 {ligand_name}.mol2
loadamberparams {ligand_name}.frcmod
check lig

prot1 = loadpdb {protein_1}.pdb
check prot1

prot2 = loadpdb {protein_2}.pdb
check prot2

{KNOWN_FORCEFIELDS[forcefield]["waterfix"]}

complex = combine {"{"} prot1 prot2 lig {"}"}
solvateOct complex {KNOWN_FORCEFIELDS[forcefield]["water"]}BOX {box}
addions complex Na+ 0
addions complex Cl- 0
savepdb complex {complex_out}.pdb

saveamberparm complex {complex_out}.parm7 {complex_out}.rst7

protein = combine {"{"} prot1 prot2 {"}"}
solvateOct protein {KNOWN_FORCEFIELDS[forcefield]["water"]}BOX {box}
addions protein Na+ 0
addions protein Cl- 0
savepdb protein {protein_out}.pdb

saveamberparm protein {protein_out}.parm7 {protein_out}.rst7

quit"""
    return file
