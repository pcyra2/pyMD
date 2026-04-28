"""
#TODO
"""
import os
import subprocess
import numpy


import pymd.tools.io as io
from pymd.tools.structure import Molecule


def gen_gaussian_for_antechamber(mol: Molecule, proc: int=12, mem: int=10) -> str:
    """Generates a Gaussian input file for a geometry optimisation and ESP calculation for use in antechamber.
    
    Args:
        mol (Molecule): The molecule to generate the input file for. This should have the
            charge and spin attributes set, as well as the Name attribute.
        proc (int): The number of processors to use for the calculation. Defaults to 12.
        mem (int): The amount of memory to use for the calculation in GB. Defaults to 10 GB.
     Returns:
         str: The contents of the Gaussian input file.
    """

    assert isinstance(mol.charge, int)
    assert isinstance(mol.spin, int)
    assert isinstance(proc, int)
    assert isinstance(mem, int)

    file = f"""%Chk=geo_opt.chk
%Mem={mem}GB
%NProc={proc}
#p opt b3lyp/6-31G(d,p) SCF=XQC nosymm

{mol.Name} geo opt

{mol.charge} {int(mol.spin+1)}
{mol.print_coords()}

--link1--
%OldChk=geo_opt.chk
%Chk=esp.chk
%NoSave
%Mem={mem}GB
%NProc={proc}
#p b3lyp/6-31G(d,p) Geom=Check nosymm iop(6/33=2) pop(chelpg,regular) EmpiricalDispersion=GD3

{mol.Name} esp

{mol.charge} {int(mol.spin + 1)}
"""
    return file



def run_antechamber(
        path: str,
        lig_code: str,
        charge: int,
        mult: int) -> None:
    """
    Runs antechamber on a gaussian log file to generate a mol2 file with RESP charges, then runs 
    parmchk2 to generate the frcmod file for the ligand. The original mol2 file is also updated 
    with the RESP charges.

    Args:
        path (str): Path to perform the anterchamber calculation in. This should contain the 
            gaussian log file generated from the gen_gaussian_for_antechamber function and 
            the original mol2 file.
        lig_code (str): The code for the ligand. This should also be the prefix of the original 
            mol2 file and the gaussian log file.
        charge (int): The charge of the ligand.
        mult (int): The multiplicity of the ligand. (2S+1)
    """
    os.system(command=f"cd {path} ; antechamber -i {lig_code}.log -fi gout -o " \
              + f"{lig_code}_dft.mol2 -fo mol2 -c resp -nc {charge}, -m {mult}")
    charge_lines = io.text_read(path=os.path.join(path,f"{lig_code}_dft.mol2"))
    coord_lines = io.text_read(path=os.path.join(path,f"{lig_code}.mol2"))
    num_atoms = int(charge_lines[2].split()[0])
    charges = numpy.zeros(num_atoms)
    atom_lines = 0
    charge_line = 0
    for i, line in enumerate(iterable=coord_lines):
        if line.startswith("@<TRIPOS>ATOM"):
            atom_lines = i+1
            break
    for i, line in enumerate(iterable=charge_lines):
        if line.startswith("@<TRIPOS>ATOM"):
            charge_line = i+1
            break
    
    for index, line in enumerate(iterable=charge_lines[charge_line:charge_line+num_atoms]):
        chg = line.split()[8]
        charges[index] = chg

    topfile = coord_lines[:atom_lines]
    bottomfile = coord_lines[num_atoms+atom_lines:]
    middlefile: list[str] = [str]*num_atoms

    for index, line in enumerate(iterable=coord_lines[atom_lines:num_atoms+atom_lines]):
        print(line)
        atom_line = line[:70]
        middlefile[index] = atom_line + str(charges[index])

    lines = topfile + middlefile + bottomfile

    io.text_dump(text=lines, path=os.path.join(path,f"{lig_code}.mol2"))
    subprocess.run(args=[ "antechamber", "-fi", "mol2", "-i", f"{lig_code}.mol2", "-fo", "mol2", "-o",
                    f"{lig_code}_ac.mol2", "-at", "gaff2", "-an", "n", "-du", "n", "-pf", "y" ],
                    cwd=path, check=True)

    os.system(command=f"cd {path} ; parmchk2 -i {lig_code}_ac.mol2 -f mol2 -o {lig_code}_ac.frcmod -a Y -s gaff2") #TODO Change to subprocess.run

    os.remove(path=os.path.join(path, "ANTECHAMBER.FRCMOD"))
    subprocess.run(args=["sed", "-i", "'s/ Cl/ CL/g'", f"{lig_code}_ac.mol2"], cwd=path, check=False)
