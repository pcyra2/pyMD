from  dataclasses import dataclass
import shutil
import os
import hashlib
import glob

from pymd.experiments.md.replica_md.helpers import recipies
from pymd.tools import io, structure



# @dataclass
class config:
    input_dir: str = "UserInput"
    ligand_file: str = "MOH.mol2"
    ligand_code: str = "MOH"
    lig_charge_spin: tuple[int,int] = (0,0) # Tuple of (charge, spin)
    protein_file: str = "protein.pdb"
    waters_file: str = "waters.pdb"
    ions_file: str = "ions.pdb"
    parmfile: str = "system.parm7"
    start_structure: str = "system.rst7"
    base_pdb: str = "system.pdb"
    cpus: int = 12
    gpus: int = 1
    memory: int = 20
    waters: str = "tip3p"
    status_file: str = "status.json"
    temperature: float = 300.0
    production_time: float = 100 # Time in ns
    replicas: int = 4 # Number of production repicas to run
    hpc_partition: str = "compchemq"
    hpc_modules: list[str] = ["cuda-12.2.2","amber-uon/gcc11.3.0/24" ]
    hpc_base_path: str = "/gpfs01/home/brara83/pyMD_WorkDir/"



def main():
    hpc_path = os.path.join(config.hpc_base_path, hashlib.md5(os.getcwd().encode()).hexdigest())

    hpc = recipies.init_hpc(config=config)
    hpc.define_dirs(local_file_path=os.getcwd(), hpc_file_path=hpc_path)
    hpc.hpc.make_dir(hpc.hpc_run_dir)
    STATUS = recipies.init_status(config=config)

    

    
    
    if os.path.isfile(os.path.join(config.input_dir, config.base_pdb)) is False: # Perform parameterisation
        if hasattr(STATUS, "parameterisation") is False:
            STATUS.add_stage(stage="parameterisation", steps=["file_man","lig_prep", "leap"])

        if STATUS.get_status("parameterisation", "file_man") != "complete":
            io.make_dir("Setup")
            input_files = glob.glob(os.path.join(config.input_dir, "*"))
            ligand = False
            for i in input_files:
                shutil.copy(i, os.path.join("Setup", os.path.basename(i)))
                print(i)
                if config.ligand_file in i:
                    ligand = True
            if ligand is False: # No ligand is present, skip ligand parameterisation
                STATUS.update_step("parameterisation", "lig_prep", "complete")

            STATUS.update_step("parameterisation", "file_man", "complete")
        
        if STATUS.get_status("parameterisation", "lig_prep") != "complete":
            recipies.gen_lig_parms(config=config, hpc_path=hpc_path, STATUS=STATUS)
        if STATUS.get_status("parameterisation", "leap") != "complete":
            STATUS = recipies.run_leap(config=config, STATUS=STATUS)
            if STATUS.get_status("parameterisation", "leap") != "ERROR":
                for i in [config.base_pdb, config.parmfile, config.start_structure]:
                    shutil.copy(os.path.join("Setup", i), os.path.join(os.getcwd(), i))
                STATUS.update_step("parameterisation", "leap", "complete")
            else:
                print("ERROR: Leap failed, check the log file for details.")
                quit()
            

            
    md = recipies.init_md(config=config)
    pre_prod_path = "./pre_prod"
    md = recipies.pre_prod(md=md, config=config, run_dir=pre_prod_path)
            
    
    if hasattr(STATUS, "setup") is False:
        steps = ["file_man"]
        for job in md.jobs:
            steps.append( job.inputfile_name.replace(".in",""))
        STATUS.add_stage(stage="setup", steps=steps)
    
    if STATUS.get_status("setup", "file_man") != "complete":
        io.make_dir(pre_prod_path)
        for i in [config.base_pdb, config.parmfile, config.start_structure]:
            shutil.copy(i, os.path.join(pre_prod_path, i))
        STATUS.update_step("setup", "file_man", "complete" )
        
    for job in md.jobs:
        step_name = job.inputfile_name.replace(".in","")
        if STATUS.get_status("setup", step_name) != "complete":
            job.exe()
            STATUS.update_step("setup", step_name, "complete" )
    

    production_path = "./prod"
    if hasattr(STATUS, "production") is False:
        steps = ["setup"]
        for i in range(config.replicas):
            steps.append(f"prod_{i+1}")
        STATUS.add_stage(stage="production", steps=steps)
    
    prod_start_structure = md.jobs[-1].inputfile_name.replace(".in", "")+".ncrst"
    # hpc = DEFAULT_HPC
    if STATUS.get_status("production", "setup") != "complete":
        io.make_dir(production_path)
        shutil.copy(os.path.join(pre_prod_path, prod_start_structure), os.path.join(production_path, prod_start_structure))
        shutil.copy(os.path.join(pre_prod_path, config.parmfile), os.path.join(production_path, config.parmfile))
        hpc.hpc.make_dir(hpc.hpc_run_dir)
        hpc.hpc.sync(work_dir=hpc.local_file_dir, hpc_work_dir=hpc.hpc_run_dir, direction="forward")
        hpc.define_dirs(local_file_path=production_path, hpc_file_path=os.path.join(hpc.hpc_run_dir,production_path))
        hpc.hpc.make_dir(hpc.hpc_run_dir)
        STATUS.update_step("production", "setup", "complete" )
    
    for i in range(config.replicas):
        name = f"prod_{i+1}"
        md, STATUS = recipies.production(md=md, STATUS=STATUS, config=config, name=name, hpc=hpc, start_structure= prod_start_structure, run_dir=production_path)
    
if __name__ == "__main__":
    main()
