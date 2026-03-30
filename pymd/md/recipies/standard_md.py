"""
#TODO
"""

import os

import pymd.tools.convert as convert
from pymd.md.md import MDClass

def initialise_system(mm: MDClass,
        min_steps: int=10000,
        heat_steps: int=convert.time_to_steps(sim_time=20, time_units="ps", timestep=0.002),
        nvt_steps: int=convert.time_to_steps(sim_time=100, time_units="ps", timestep=0.002),
        npt_steps: int=convert.time_to_steps(sim_time=10, time_units="ns", timestep=0.002),
        temperature: float=300.0,
        pressure: float = 1.0,
        path: str="./",
        execute:bool = False) -> MDClass:
    """
    Runs a standard MD protocol. This starts with a solvation minimisation, followed by a 
    full system minimisation. Then the system is heated for 90% of the heating time, followed by NVT 
    equilibration. Then an additional NVT and NPT equilibration. 

    Args:
        mm (MDClass): The MDClass object that contains the system information.
        min_steps (int, optional): The number of steps to minimize the complete system. 
            An additional 2000 steps are performs on the solvent ONLY. Defaults to 10000.
        heat_steps (int, optional): The number of steps to heat the system for. The timestep will be 2 fs. 
            Defaults to convert.time_to_steps(20, "ps", 0.002).
        nvt_steps (int, optional): The number of steps for the NVT equilibration. 
            Defaults to convert.time_to_steps(100, "ps", 0.002).
        npt_steps (int, optional): The number of steps for the NPT equilibration. 
            Defaults to convert.time_to_steps(10, "ns", 0.002).
        temperature (float, optional): The temperature to run the simulations at (post heating). 
            Defaults to 300.0.
        pressure (float, optional): The pressure to run the NPT enseble at. Defaults to 1.0.
        path (str, optional): The path to run the simulations. Defaults to "./".
        execute (bool, optional): Whether to run the simulation after generating. Defaults to False.

    Returns:
        MDClass: The MD Class object with the jobs generated.
    """
    assert os.path.exists(path=path), f"Path {path} does not exist"

    mm.minimize(input_structure="start.rst7",
                job_name="min1", steps=2000,
                restraints="'!(WAT NA+ CL-)'",
                run_path=path)

    mm.minimize(input_structure="min1.rst7",
                job_name="min2",
                steps=min_steps,
                run_path=path)

    mm.heat(input_structure="min2.rst7",
            job_name="heat",
            steps=heat_steps,
            start_temperature=0.0,
            end_temperature=temperature)

    mm.constant(input_structure="heat.rst7",
                job_name="NVT1",
                steps=nvt_steps,
                temperature=temperature,
                traj_out=int(nvt_steps/100))

    mm.constant(input_structure="NVT1.rst7",
                job_name="NPT1",
                steps=npt_steps,
                temperature=temperature,
                pressure=pressure,
                traj_out=int(npt_steps/100))

    if execute:
        for job in mm.jobs:
            job.exe()

    return mm
