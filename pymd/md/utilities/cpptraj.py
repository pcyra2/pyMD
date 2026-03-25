"""Pythonic interface to the CPPTRAJ code that is bundled with AmberTools. 
This predominantly generates input files but also is bundled with an executor. 
"""

import os
import subprocess

import pymd.tools.io as io


def extract_ligand(
        parm_file: str,
        structure_file: str,
        resid: int,
        output_file: str) -> str:
    """Uses cpptraj to extract a ligand. Strips all atoms that aren't the resid.

    Args:
        parm_file (str): Name of parameter file, including file extension.
        structure_file (str): Name of topology file, including file extension.
        resid (int): The residue ID of the ligand.
        output_file (str): The name of the output structure file. 
            This should contain the file extension.
    """
    file = f"""parm {parm_file}
trajin {structure_file}

strip !:{resid}
trajout {output_file}

run
"""
    return file

def extract_protein(
    parm_file: str,
    structure_file: str,
    resid: int,
    output_file: str
    ) -> str:
    """

    Args:
        parm_file (str): _description_
        structure_file (str): _description_
        resid (int): _description_
        output_file (str): _description_
    """
    file = f"""parm {parm_file}
trajin {structure_file}

strip !:1-{resid}

trajout {output_file}

run
"""
    return file


def run_cpptraj(
        job_file: str,
        cpptraj_out: str,
        cpptraj_in: str = "cpptraj.in",
        path: str = "./") -> None:
    """#TODO
    """
    io.text_dump(text=job_file, path=os.path.join(path, cpptraj_in))
    with open(file=os.path.join(path, cpptraj_out), mode="w", encoding="UTF-8") as f:
        subprocess.run(args=["cpptraj", "-i", cpptraj_in], cwd=path, stdout=f, check=True)
