import os
import pyMD.tools.io as io
import pyMD.tools.convert as convert
from pyMD.MD.MD import MDClass

def initialise_system(MM: MDClass, 
        min_steps: int=10000, 
        heat_steps: int=convert.time_to_steps(20, "ps", 0.002), 
        nvt_steps: int=convert.time_to_steps(100, "ps", 0.002), 
        npt_steps: int=convert.time_to_steps(10, "ns", 0.002), 
        temperature: float=300.0,
        pressure: float = 1.0,
        path: str="./", 
        execute:bool = False)->MDClass:
	assert os.path.exists(path), f"Path {path} does not exist" 
    
	MM.minimize("start.rst7", "min1", 2000, "'!(WAT NA+ CL-)'", run_path=path)

	MM.minimize("min1.rst7", "min2", min_steps, run_path=path)

	MM.heat("min2.rst7", "heat", heat_steps, 0.0, temperature)

	MM.constant("heat.rst7", "NVT1", steps=nvt_steps, temperature=temperature, traj_out=int(nvt_steps/100)) 

	MM.constant("NVT1.rst7", "NPT1", steps=npt_steps, temperature=temperature, pressure=pressure, traj_out=int(npt_steps/100))

	if execute:
		for job in MM.jobs:
			job.exe()

	return MM
