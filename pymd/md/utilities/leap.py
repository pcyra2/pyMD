"""
Contains a python interface to tleap. This predominantly generates input files but 
also dictates the correct water forcefields for a given global forcefield. 
"""

import subprocess
import os
import pymd.tools.io as io

KNOWN_FORCEFIELDS: dict[str, dict[str, str]] = dict(ff14SB = dict(phosaa = "phosaa14SB",
                                    water = "TIP3P",
                                    ),
                        ff19SB = dict(phosaa = "phosaa19SB",
                                    water = "OPC",
                                    ) # Potentially need the water fix
                                    )
PARAMETER_FILES: dict[str, str] = dict(
    ff14SB = "leaprc.protein.ff14SB",
    ff19SB = "leaprc.protein.ff19SB",
    TIP3P = "leaprc.water.tip3p",
    TIP4P = "leaprc.water.tip4p",
    OPC = "leaprc.water.opc",
    phosaa14SB = "leaprc.phosaa14SB",
    phosaa19SB = "leaprc.phosaa19SB",
    gaff = "leaprc.gaff",
    gaff2 = "leaprc.gaff2")

def gen_leap(protein_file:str,
            ligand_name:str|None = None,
            waters: str|None = None,
            ions: str|None = None,
            parm_file: str = "complex.parm7",
            amber_coor: str = "complex.rst7",
            forcefield: str = "ff14SB",
            gaff: None|str = "gaff",
            water: None|str = "TIP3P",
            box: float = 12.0,
            extra_parms: list[str] = []
            ) -> str:
    """
    """

    assert forcefield in KNOWN_FORCEFIELDS.keys()
    file = f"source {PARAMETER_FILES[forcefield]}\n"

    if water is None:
        water = KNOWN_FORCEFIELDS[forcefield]["water"]
    file += f"source {PARAMETER_FILES[water]}\n"

    if gaff is not None:
        file += f"source {PARAMETER_FILES[gaff]}\n"

    for parm in extra_parms:
        file += f"source {PARAMETER_FILES[parm]}\n"
    complex = "prot "
    if ligand_name is not None:
        complex += " lig"
        file += f"""
lig = loadmol2 {ligand_name}_ac.mol2
loadamberparams {ligand_name}_ac.frcmod
check lig"""
    if waters is not None:
        complex += " wat"
        file += f"""
wat = loadpdb {waters}
check wat"""
    if ions is not None:
        complex += " ion"
        file += f"""
ion = loadpdb {ions}
check ion"""
    file += f"""
prot = loadpdb {protein_file}
check prot

complex = combine {"{"} {complex} {"}"}
solvateOct complex {water}BOX {box}
addions complex Na+ 0
savepdb complex {parm_file.replace(".parm7", ".pdb")}
saveamberparm complex {parm_file} {amber_coor}
quit"""
    return file

def run_leap(path: str, file: str = "leap.in") -> None:
    """
    Runs tleap on the leap.in file

    Args:
        path (str): location of the leap.in file
    """
    print(f"INFO: Running tleap -f {file} > {file.replace('.in', '.log')} in {path}")
    with open(os.path.join(path, file.replace(".in", ".log")), "w") as f:
        subprocess.run(args=["tleap", "-f", file], cwd = path,
                            text = True, stdout=f, check=True)

def gen_leap_ti(
        ligand_name: str,
        protein_1: str,
        protein_2: str,
        complex_out: str = "complex",
        protein_out: str = "protein",
        forcefield: str = "ff14SB",
        box: float = 12.0,
        gaff: str|None = "gaff", 
        water: str|None = "TIP3P",
        extra_parms: list[str] = []) -> str:
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

    file = f"source {PARAMETER_FILES[forcefield]}\n"

    if water is None:
        water = KNOWN_FORCEFIELDS[forcefield]["water"]
    file += f"source {PARAMETER_FILES[water]}\n"

    if gaff is not None:
        file += f"source {PARAMETER_FILES[gaff]}\n"

    for parm in extra_parms:
        file += f"source {PARAMETER_FILES[parm]}\n"
    file += f"""
lig = loadmol2 {ligand_name}.mol2
loadamberparams {ligand_name}.frcmod
check lig

prot1 = loadpdb {protein_1}
check prot1

prot2 = loadpdb {protein_2}
check prot2

complex = combine {"{"} prot1 prot2 lig {"}"}
solvateOct complex {water}BOX {box}
addions complex Na+ 0
addions complex Cl- 0
savepdb complex {complex_out}.pdb

saveamberparm complex {complex_out}.parm7 {complex_out}.rst7

protein = combine {"{"} prot1 prot2 {"}"}
solvateOct protein {water}BOX {box}
addions protein Na+ 0
addions protein Cl- 0
savepdb protein {protein_out}.pdb

saveamberparm protein {protein_out}.parm7 {protein_out}.rst7

quit"""
    return file

def check_leap_log(path: str, file: str = "leap.log"):
    if os.path.isfile(path=os.path.join(path, file)) is False:
        return False
    logfile = io.text_read(path=os.path.join(path, file))
    final_line = logfile[-1]
    if final_line.startswith(f"Exiting LEaP:") is False:
        return False
    dat = final_line.split()
    errs = int(dat[4].replace(";",""))
    if errs > 0:
        print(f"ERROR: Number of errors in leap file is {errs}")
        return False
    return True
