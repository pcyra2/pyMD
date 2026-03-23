import pyMD.tools.io as io
import os
import subprocess

def extract_ligand(parmfile: str, 
                structurefile: str, 
                resid: int, 
                outputfile: str):
    file = f"""parm {parmfile}
trajin {structurefile}

strip !:{resid}
trajout {outputfile}

run
"""
    return file

def extract_protein(
    parmfile: str,
    structurefile: str, 
    resid: int,    
    outputfile: str
    ):
    """

    Args:
        parmfile (str): _description_
        structurefile (str): _description_
        resid (int): _description_
    """
    file = f"""parm {parmfile}
trajin {structurefile}

strip !:1-{resid}

trajout {outputfile}

run
"""
    return file
    

def run_cpptraj(job_file: str, cpptraj_out: str, cpptraj_in: str = "cpptraj.in", path: str = "./"):
    io.textDump(job_file, os.path.join(path, cpptraj_in))
    with open(os.path.join(path, cpptraj_out), "w") as f:
        subprocess.run(["cpptraj", "-i", cpptraj_in], cwd=path, stdout=f)
