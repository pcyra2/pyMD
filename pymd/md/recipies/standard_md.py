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
    

    Args:
        mm (MDClass): _description_
        min_steps (int, optional): _description_. Defaults to 10000.
        heat_steps (int, optional): _description_. 
            Defaults to convert.time_to_steps(20, "ps", 0.002).
        nvt_steps (int, optional): _description_. 
            Defaults to convert.time_to_steps(100, "ps", 0.002).
        npt_steps (int, optional): _description_. 
            Defaults to convert.time_to_steps(10, "ns", 0.002).
        temperature (float, optional): _description_. Defaults to 300.0.
        pressure (float, optional): _description_. Defaults to 1.0.
        path (str, optional): _description_. Defaults to "./".
        execute (bool, optional): _description_. Defaults to False.

    Returns:
        MDClass: _description_
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
