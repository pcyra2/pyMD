from pyMD.MD.MD import MDClass
import pyMD.tools.io as io
from pyMD.tools.structure import molecule

import subprocess
import os
import numpy

KNOWN_FORCEFIELDS = dict(ff14SB = dict(phosaa = "phosaa14SB",
                                    water = "TIP3P",
                                    waterff = "leaprc.water.tip3p",
                                    waterfix = ""), 
                        ff19SB = dict(phosaa = "phosaa19SB",
                                    water = "OPC",
                                    waterff = "leaprc.water.opc",
                                    waterfix = "set default FlexibleWater on")
                                    )

def gen_gaussian(mol: molecule, proc: int=12, mem: int=10):
    
    assert type(mol.charge) == int
    assert type(mol.spin) == int
    assert type(proc) == int
    assert type(mem) == int

    file = f"""%Chk=geo_opt.chk
%Mem={mem}GB
%NProc={proc}
#p opt b3lyp/6-31G(d,p) SCF=XQC nosymm

NTA geo opt

{mol.charge} {int(mol.spin+1)}
{mol.print_coords()}

--link1--
%OldChk=geo_opt.chk
%Chk=esp.chk
%NoSave
%Mem={mem}GB
%NProc={proc}
#p b3lyp/6-31G(d,p) Geom=Check nosymm iop(6/33=2) pop(chelpg,regular) EmpiricalDispersion=GD3

NTA esp

{mol.charge} {int(mol.spin + 1)}
"""
    return file

def gen_leap(LigCode:str, 
            pdb_file:str, 
            parmfile: str, 
            ambercoor: str = "start.rst7", 
            forcefield: str = "ff14SB", 
            box: float = 12.0
            ):
    assert forcefield in KNOWN_FORCEFIELDS.keys(), f"ERROR: Forcefield {forcefield} unknown"

    file = f"""source leaprc.protein.{forcefield}
source leaprc.{KNOWN_FORCEFIELDS[forcefield]["phosaa"]}
source {KNOWN_FORCEFIELDS[forcefield]["waterff"]}

lig = loadmol2 {LigCode}_ac.mol2
loadamberparams {LigCode}_ac.frcmod
check lig

prot = loadpdb {pdb_file}
check prot

{KNOWN_FORCEFIELDS[forcefield]["waterfix"]}

complex = combine {"{"} prot lig {"}"} 
solvateOct complex {KNOWN_FORCEFIELDS[forcefield]["water"]}BOX {box}
addions complex Na+ 0
savepdb complex complex.pdb
saveamberparm complex {parmfile} {ambercoor}
quit"""
    return file

def run_leap(path: str):
    """
    Runs tleap on the leap.in file

    Args:
        path (str): location of the leap.in file
    """
    log = subprocess.run(["tleap", "-f", "leap.in"], cwd = path,
                            text = True, capture_output = True)
    io.textDump(log.stdout, os.path.join(path, "leap.log"))

def run_antechamber(path: str, LigCode: str, charge: int, mult: int):

    os.system(f"cd {path} ; antechamber -i {LigCode}.log -fi gout -o {LigCode}_dft.mol2 -fo mol2 -c resp -nc {charge}, -m {mult}")
    charge_lines = io.textRead(os.path.join(path,f"{LigCode}_dft.mol2"))
    coord_lines = io.textRead(os.path.join(path,f"{LigCode}.mol2"))
    num_atoms = int(charge_lines[2].split()[0])
    charges = numpy.zeros(num_atoms)
    for index, line in enumerate(charge_lines[8:num_atoms+8]):
        chg = line.split()[8]
        charges[index] = chg

    topfile = coord_lines[:8]
    bottomfile = coord_lines[num_atoms+8:]
    middlefile: list[str] = []*num_atoms

    for index, line in enumerate(coord_lines[8:num_atoms+8]):
        atom_line = line[:70]
        middlefile[index] = atom_line + str(charges[index])
    
    lines = topfile + middlefile + bottomfile

    io.textDump(lines, os.path.join(path,f"{LigCode}.mol2"))
    # os.system(f"cd {path} ; antechamber -fi mol2 -i {LigCode}.mol2 -fo mol2 -o {LigCode}_ac.mol2 -at gaff2 -an n -du n -pf y ")
    subprocess.run([ "antechamber", "-fi", "mol2", "-i", f"{LigCode}.mol2", "-fo", "mol2", "-o", f"{LigCode}_ac.mol2", "-at", "gaff2", "-an", "n", "-du", "n", "-pf", "y" ], cwd=path)

    os.system(f"cd {path} ; parmchk2 -i {LigCode}_ac.mol2 -f mol2 -o {LigCode}_ac.frcmod -a Y -s gaff2")

    os.remove(os.path.join(path, "ANTECHAMBER.FRCMOD"))
    subprocess.run(["sed", "-i", "'s/ Cl/ CL/g'", f"{LigCode}_ac.mol2"], cwd=path)