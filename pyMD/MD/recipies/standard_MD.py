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
            path: str="./", 
            execute:bool = False)->MDClass:
    assert os.path.exists(path), f"Path {path} does not exist" 
    
    MM.minimize("start.rst7", "min1", 2000, "'!(WAT NA+ CL-)'", run_path=path)

    MM.minimize("min1.rst7", "min2", min_steps, run_path=path)

    MM.heat("min2.rst7", "heat", heat_steps, 0.0, 300.0)

    return MM
    
    # MM.heat("min2.rst7", "heat", heat_time, 0.0, temperature, restraints="'!(WAT NA+ CL-)'")
    # io.textDump(MM.jobs["heat"]["inputfile"], path+"./heat.inp")
    
    # if execute:
    #     MM.run_MD( path+"./heat.inp",  path+"./heat.out", False)

    # MM.constant("heat.rst7", "NVT1", nvt_time, 100, temperature=temperature)
    # io.textDump(MM.jobs["heat"]["inputfile"], path+"./NVT1.inp")

    # if execute:
    #     MM.run_MD( path+"./NVT1.inp",  path+"./NVT1.out", False)

    # MM.constant("NVT1.rst7", "NPT1", npt_time, 100, pressure="on", temperature=temperature)
    # io.textDump(MM.jobs["NPT1"]["inputfile"], path+"./NPT1.inp",)
    
    # if execute:
    #     MM.run_MD( path+"./NPT1.inp",  path+"./NPT1.out", False)