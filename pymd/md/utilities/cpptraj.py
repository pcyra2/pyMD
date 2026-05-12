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
        output_file: str,
        path: str = "./")  -> None:
    """Uses cpptraj to extract a ligand. Strips all atoms that aren't the resid.

    Args:
        parm_file (str): Name of parameter file, including file extension.
        structure_file (str): Name of topology file, including file extension.
        resid (int): The residue ID of the ligand.
        output_file (str): The name of the output structure file. 
            This should contain the file extension.
        path (str): The path to run the cpptraj calculation in. Defaults to `./`.
    
    """
    file = f"""parm {parm_file}
trajin {structure_file}

strip !:{resid}
trajout {output_file}

run
"""
    
    run_cpptraj(job_file=file,
                cpptraj_in="ligand_extract.in",
                cpptraj_out="ligand_extract.out", 
                path=path)

def extract_protein(
    parm_file: str,
    structure_file: str,
    resid: int,
    output_file: str
    ) -> str:
    """#TODO

    Args:
        parm_file (str): The parameter file for the system.
        structure_file (str): The topology file for the system.
        resid (int): The resid for the last residue in the protein.
        output_file (str): The name of the output file for the extracted protien. 
            This should contain the file extention.
    """
    file = f"""parm {parm_file}
trajin {structure_file}

strip !:1-{resid}

trajout {output_file}

run
"""
    return file

def _rmsd_protein_backbone() -> str:
    return f"rmsd backbone_rmsd @C,CA,N out backbone_RMSD refererence\n"

def _set_reference(file: str) -> str:
    return f"reference {file}\n"

def trajectory_analysis(
        parm_file: str,
        trajectories: list[str],
        reference: str|None,
        ) -> list[str]:
    file = f"parm {parm_file}\n"
    for traj in trajectories:
        file += f"trajin {traj}\n"
    if reference is not None:
        file += _set_reference(file=reference)


def run_cpptraj(
        job_file: str|list[str],
        cpptraj_out: str,
        cpptraj_in: str = "cpptraj.in",
        path: str = "./") -> None:
    """Runs a cpptraj file.

    Args:
        job_file (str | list[str]): The contents of the input file to send to cpptraj.
        cpptraj_out (str): The output file for the logging of cpptraj.
        cpptraj_in (str): The name of the input file for the logging of cpptraj.
        path (str): The path to run the simulation.
    """
    print(f"INFO: Running cpptraj -i {cpptraj_in} > {cpptraj_out} in {path}")
    io.text_dump(text=job_file, path=os.path.join(path, cpptraj_in))
    with open(file=os.path.join(path, cpptraj_out), mode="w", encoding="UTF-8") as f:
        subprocess.run(args=["cpptraj", "-i", cpptraj_in], cwd=path, stdout=f, check=True)

def to_pdb(structure_file: str, parm_file: str, pdb_name: str, path: str = "./"):
    file = f"""parm {parm_file}
trajin {structure_file}
autoimage
trajout {pdb_name}

run
"""
    print(f"INFO: Running cpptraj to convert {structure_file} to pdb in {path}")
    io.text_dump(file, os.path.join(path, "to_pdb.in"))
    with open(os.path.join(path, "to_pdb.log"), "w") as f:
        subprocess.run(args=["cpptraj", "-i", "to_pdb.in"], cwd=path, stdout=f, check=True)

def strip(key: str,
        structure_file: str,
        parm_file: str,
        output: str,
        path: str = "./"):
    """Strips contents from a structure/trajectory file using cpptraj. This can be used to strip solvent from a trajectory for example.
    
    Args:
        key (str): The cpptraj strip command to specify what to strip. For example, to strip solvent, this would be "WAT".
        structure_file (str): The name of the structure/trajectory file to strip.
        parm_file (str): The parameter file for the system.
        output (str): The name of the output file after stripping.
        path (str): The path to run the cpptraj calculation in. Defaults to `./`.
    """
    file = f"""parm {parm_file}
trajin {structure_file}
strip {key}

trajout {output}
run
"""
    print(f"INFO: Running cpptraj to strip {key} from {structure_file} in {path}")
    io.text_dump(file, os.path.join(path, "strip.in"))
    with open(os.path.join(path, "strip.log"), "w") as f:
        subprocess.run(args=["cpptraj", "-i", "strip.in"], cwd=path, stdout=f, check=True)