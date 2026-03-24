import os

import pymd.tools.convert as convert
from pymd.md.md import MDClass

def initialise_system(mm: MDClass,
        min_steps: int=10000,
        heat_steps: int=convert.time_to_steps(20, "ps", 0.002),
        nvt_steps: int=convert.time_to_steps(100, "ps", 0.002),
        npt_steps: int=convert.time_to_steps(10, "ns", 0.002),
        temperature: float=300.0,
        pressure: float = 1.0,
        path: str="./",
        execute:bool = False)->MDClass:
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
    assert os.path.exists(path), f"Path {path} does not exist"

    mm.minimize("start.rst7",
                "min1", 2000,
                "'!(WAT NA+ CL-)'",
                run_path=path)

    mm.minimize("min1.rst7",
                "min2",
                min_steps,
                run_path=path)

    mm.heat("min2.rst7",
            "heat",
            heat_steps,
            0.0,
            temperature)

    mm.constant("heat.rst7",
                "NVT1",
                steps=nvt_steps,
                temperature=temperature,
                traj_out=int(nvt_steps/100))

    mm.constant("NVT1.rst7",
                "NPT1",
                steps=npt_steps,
                temperature=temperature,
                pressure=pressure,
                traj_out=int(npt_steps/100))

    if execute:
        for job in mm.jobs:
            job.exe()

    return mm
