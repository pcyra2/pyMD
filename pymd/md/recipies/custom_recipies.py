import os
from runpy import run_path

import pymd.tools.convert as convert
from pymd.md.md import MDClass

def qian_init_system(mm: MDClass, path: str, protein_max_resid: int) -> MDClass:
    """
    Args:
        mm (MDClass): The MDClass object that contains the system information.

            Returns:
        MDClass: The MD Class object with the jobs generated.
    """
    assert os.path.exists(path=path), f"Path {path} does not exist"

    mm.minimize(input_structure="complex.rst7", 
                    job_name="min1",
                    steps=10000,
                    restraints=f"':1-{protein_max_resid}'",
                    run_path=path,
                    steps_steepest=5000,
                    traj_out=0, 
                    restart_out=500,
                    energy_out=10
                    )
    mm.minimize(input_structure="min1.rst7", 
                    job_name="min2",
                    steps=10000,
                    restraints=None,
                    run_path=path,
                    steps_steepest=5000,
                    traj_out=0, 
                    restart_out=500,
                    energy_out=10
                    )
    
    mm.heat(input_structure="min2.rst7",
            job_name="heat",
            steps=250000,
            start_temperature=0.0,
            end_temperature=318.15,
            restraints=f"':1-{protein_max_resid}'",
            traj_out=100,
            energy_out=100,
            path=path,
            thermostat=3)
    
    mm.constant(input_structure="heat.rst7",
                job_name="nvt",
                steps=500000,
                temperature=318.15,
                restraints=f"':1-{protein_max_resid}'",
                path=path,
                traj_out=10000,
                energy_out=1000,
                restart_out=1000
                )
    mm.constant(input_structure="nvt.rst7",
                job_name="npt1",
                steps=500000,
                temperature=318.15,
                pressure=-1,
                barostat=2,
                restraints=f"'@CA,N,C'",
                path=path,
                traj_out=10000,
                energy_out=1000,
                restart_out=1000
                )
    mm.constant(input_structure="npt1.rst7",
                job_name="npt2",
                steps=500000,
                temperature=318.15,
                pressure=-1,
                barostat=2,
                restraints=None,
                path=path,
                traj_out=10000,
                energy_out=1000,
                restart_out=1000
                )
    mm.constant(input_structure="npt2.rst7",
                job_name="npt3",
                steps=500000,
                temperature=318.15,
                pressure=1.0,
                barostat=2,
                restraints=None,
                path=path,
                traj_out=10000,
                energy_out=1000,
                restart_out=1000
                )
    

    return mm