"""
#TODO
"""
import os
import subprocess
import numpy


import pymd.tools.io as io
from pymd.tools.structure import Molecule


def gen_gaussian(mol: Molecule, proc: int=12, mem: int=10):
    """#TODO"""

    assert isinstance(mol.charge, int)
    assert isinstance(mol.spin, int)
    assert isinstance(proc, int)
    assert isinstance(mem, int)

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



def run_antechamber(
        path: str,
        lig_code: str,
        charge: int,
        mult: int):
    """
    #TODO

    Args:
        path (str): _description_
        lig_code (str): _description_
        charge (int): _description_
        mult (int): _description_
    """
    os.system(f"cd {path} ; antechamber -i {lig_code}.log -fi gout -o " \
              + f"{lig_code}_dft.mol2 -fo mol2 -c resp -nc {charge}, -m {mult}")
    charge_lines = io.text_read(os.path.join(path,f"{lig_code}_dft.mol2"))
    coord_lines = io.text_read(os.path.join(path,f"{lig_code}.mol2"))
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

    io.text_dump(lines, os.path.join(path,f"{lig_code}.mol2"))
    subprocess.run([ "antechamber", "-fi", "mol2", "-i", f"{lig_code}.mol2", "-fo", "mol2", "-o",
                    f"{lig_code}_ac.mol2", "-at", "gaff2", "-an", "n", "-du", "n", "-pf", "y" ],
                    cwd=path, check=True)

    os.system(f"cd {path} ; parmchk2 -i {lig_code}_ac.mol2 -f mol2 -o {lig_code}_ac.frcmod -a Y -s gaff2") #TODO Change to subprocess.run

    os.remove(os.path.join(path, "ANTECHAMBER.FRCMOD"))
    subprocess.run(["sed", "-i", "'s/ Cl/ CL/g'", f"{lig_code}_ac.mol2"], cwd=path, check=True)
