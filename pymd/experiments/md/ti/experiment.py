"""
This script should automatically run thermodynamic integration.
"""
import os
import shutil
import hashlib
import sys
from dataclasses import dataclass

from pymd.experiments.md.ti.helpers import recipies#, getdvdl_alchemlyb

import pymd.md.kernels.amber as amber
from pymd.md.recipies import thermodynamic_integration as TI
from pymd.md.utilities import leap, cpptraj, parmed
from pymd.tools import io, pdb, slurm
from pymd.tools.status_tracker import StatusTracker
from pymd.user_configs.hpc_defaults import DEFAULT_HPC, SULIS



# @dataclass
class config:
    """
    Contains all the information needed to run the TI calculation.

    Attributes:
        input_file (str): File containing this class.
        input_data_dir (str): Directory where all other immutable data is contained such as input 
            protein and parameter files.
        run_dir (str): Directory to run the calculation.
        base_protein (str): File containing the wildtype protein pdb file
        base_ligand (str): File containing the wildtype ligand mol2 file. There should also be a 
            frcmod file with the same prefix in this directory. 
        mutation (str): Amino acid to mutate to.
        mutation_resid (int): Resid of residue you want to mutate.
        cpus (int): Number of cores to give a single calculation
        gpus (int) Number of GPU's to give a single calculation

    """
    input_file: str = "Job.conf"
    status_file: str = "./status.json"
    input_data_dir: str = "./input_data"
    run_dir: str = "./"
    protein_pdb: str = "Protein.pdb"
    ligand_mol2: str = "Ligand.mol2"
    start_residue: str = "GLY"
    mutation_residue: str = "HIS"
    mutation_resid: int = 4
    forcefield: str = "ff14SB"
    box: int = 10
    cpus: int = 12
    gpus: int = 1
    temperature: float = 318.0 #TODO Actually make this do something
    # hpc_name: slurm.Slurm = slurm.Slurm(partition="compchemq")
    hpc: slurm.Slurm
    hpc_name: str = "sulis_gpu"
    # hpc_base_path: str = "/gpfs01/home/brara83/pyMD_WorkDir/TI"
    hpc_base_path: str = "~/pyMD_WorkDir/TI"
    ti_windows: list[float] = [round(0 + i * 0.1,3) for i in range(11)]



def main() -> None:
    """
    Runs TI.
    """

    ## Perform some initial config stuff including setting up HPC directories.
    hpc_path = os.path.join(config.hpc_base_path, hashlib.md5(os.getcwd().encode()).hexdigest())
    config()
    if len(sys.argv) > 1:
        config.start_residue = sys.argv[1]
        config.mutation_resid = int(sys.argv[2])
        config.mutation_residue = sys.argv[3]
    if "ada" in config.hpc_name:
        partition = config.hpc_name.split("_")[1]
        config.hpc = slurm.Slurm(DEFAULT_HPC, partition=partition)
        config.hpc.set_modules(["cuda-12.2.2","amber-uon/gcc11.3.0/24" ])
    elif "sulis" in config.hpc_name:
        partition = config.hpc_name.split("_")[1]
        config.hpc = slurm.Slurm(SULIS, partition=partition)
        config.hpc.set_modules(["nottingham", "amber-uoneasy/20.11-fosscuda-2020b-AmberTools-21.3 "])
    else:
        raise ValueError(f"HPC {config.hpc_name} not recognized.")
        
    config.hpc.set_gpus(gpus=config.gpus)
    config.hpc.set_ntasks(tasks=config.cpus)
    config.hpc.set_mem(mem=20)
    config.hpc.define_dirs(local_file_path=config.run_dir, hpc_file_path=hpc_path)
    config.hpc.hpc.make_dir(hpc_path)
    # config.hpc.hpc.make_dir(hpc_path)


    ## Checks for input data directory
    assert os.path.isdir(config.input_data_dir)

    ## Initialises status tracker, either from existing file or from scratch.
    STATUS = StatusTracker(file_path =  config.status_file)
    if os.path.isfile(path=config.status_file):
        print(f"INFO: Reading job status from {config.status_file}")
        STATUS.from_dict()

    if hasattr(STATUS, "setup") is False:
        STATUS.add_stage(stage="setup", steps=["data manipulation",
                                    "leap", 
                                    "min1", 
                                    "min2",
                                    "heat", 
                                    "NVT1",
                                    "NPT1",
                                    "NPT2",])


    ## Setup the system
    setup_path = os.path.join(config.run_dir, "setup")
    io.make_dir(path=setup_path)

    shutil.copy(os.path.join(config.input_data_dir, config.protein_pdb), 
                os.path.join(setup_path, config.protein_pdb))
    shutil.copy(os.path.join(config.input_data_dir, config.ligand_mol2), 
                os.path.join(setup_path, config.ligand_mol2))
    shutil.copy(os.path.join(config.input_data_dir, config.ligand_mol2.replace("mol2", "frcmod")), 
                os.path.join(setup_path, config.ligand_mol2.replace("mol2", "frcmod")))
    
    STATUS.update_step(stage="setup", step="data manipulation", status="complete")

    ## Run initial leap step
    if STATUS.get_status(stage="setup",step="leap")!= "complete":
        print("INFO: Running initial leap step")
        leap_in = leap.gen_leap(protein_file=config.protein_pdb, ligand_name=config.ligand_mol2, forcefield=config.forcefield, water="TIP3P")

        io.text_dump(text=leap_in, path=os.path.join(setup_path, "leap.in"))
        leap.run_leap(path=setup_path)
        STATUS.update_step("setup", "leap", "run")
        tmp = leap.check_leap_log(path=setup_path)
        if tmp is True:
            STATUS.update_step("setup", "leap", "complete")
        else: 
            STATUS.update_step("setup", "leap", "error")
    

    ## Set up global md objet.
    protein_max_resid: int = pdb.get_protein_res_id_range(lines=io.text_read(path=os.path.join(setup_path, config.protein_pdb)))
    
    md = amber.Amber(start_coordinates="complex.rst7",
               parm_file="complex.parm7")
    md.describe_structure(protein_residue_start=1,
                protein_residue_end=protein_max_resid,
                )#TODO Add ligand and cofactor defenition.
    md.define_hardware(cpu = config.cpus, gpu = config.gpus)

    ## Perform initial equilibration.
    md = recipies.qian_init_system(mm=md, path=setup_path, start_structure="complex.rst7", temperature=config.temperature)
    for job in md.jobs:
        step_name = job.inputfile_name.replace(".in","")
        if STATUS.get_status(stage="setup", step=step_name) != "complete":
            job.exe(gpu=True)
            STATUS.update_step(stage="setup", step=step_name, status="complete")


    ## Define TI mutation.
    mutant_protein_path = os.path.join(config.run_dir,"mutant_structures")
    io.make_dir(mutant_protein_path)
    stage = f"mutation_{config.start_residue}_{config.mutation_resid}_{config.mutation_residue}"
    # stage = f"mutation_{config.mutation_resid}_{config.mutation_residue}"

    if hasattr(STATUS, stage) is False:
        STATUS.add_stage(stage=stage, steps=["setup","mutate","equilibrate_protein", "equilibrate_complex"])

    mutation_path = os.path.join(config.run_dir, stage)
    # config.hpc.hpc.make_dir(os.path.join(hpc_path, stage))
    mutation_setup_path = os.path.join(mutation_path,"setup")
    mutation_protein_path = os.path.join(mutation_path,"protein")
    mutation_complex_path = os.path.join(mutation_path,"complex")

    if STATUS.get_status(stage=stage, step="setup") != "complete":
        io.make_dir(path=mutation_path)
        config.hpc.hpc.make_dir(hpc_work_dir=os.path.join(hpc_path, mutation_path))
        
        io.make_dir(path=mutation_setup_path)
        io.make_dir(path=mutation_protein_path)
        io.make_dir(path=mutation_complex_path)
        
        config.hpc.hpc.make_dir(hpc_work_dir=os.path.join(hpc_path, mutation_protein_path))
        config.hpc.hpc.make_dir(hpc_work_dir=os.path.join(hpc_path, mutation_complex_path))

        shutil.copy(src=os.path.join(config.input_data_dir, config.ligand_mol2.replace("mol2", "frcmod")), 
                        dst=os.path.join(mutation_setup_path, config.ligand_mol2.replace("mol2", "frcmod")))

        ## Mutation case 1: You are mutating the wildtype, therefore you simply need to copy over the equilibrated structure.

        if config.start_residue == pdb.get_residue(lines = io.text_read(path=os.path.join(config.input_data_dir, config.protein_pdb)),
                                                   residue_number=config.mutation_resid): 
            shutil.copy(src=os.path.join(setup_path, f"{md.jobs[-1].inputfile_name}.ncrst"), 
                        dst=os.path.join(mutation_setup_path, f"{md.jobs[-1].inputfile_name}.ncrst"))
            
            shutil.copy(src=os.path.join(setup_path, md.parm_file), 
                        dst=os.path.join(mutation_setup_path, md.parm_file))

        ## Mutation case 2: You are mutating a mutant. This is the complicated case as you need to find the equilibrated mutant structure and its corresponding ligand.            

        else:
            ## Therefore you check that the mutant has been made and equilibrated.
            exists = False
            for i in STATUS._to_dict().keys():
                words = i.split("_")
                if words[0] == "mutation":
                    if words[2] == str(config.mutation_resid) and words[3] == config.start_residue:
                        exists = True
            if exists == False:
                raise ValueError(f"ERROR: Cannot mutate {config.start_residue} to {config.mutation_resid}")
            
            ## Then you copy over the equilibrated protein structure and ligand.

            shutil.copy(src=os.path.join(mutant_protein_path, f"equilibrated_mutant_{config.mutation_resid}_{config.start_residue}.pdb"),
                dst=os.path.join(mutation_setup_path, "equilibrated_complex.pdb"))
            shutil.copy(src=os.path.join(mutant_protein_path, f"Ligand_{config.mutation_resid}_{config.start_residue}.mol2"),
                dst=os.path.join(mutation_setup_path, "Ligand.mol2"))
        STATUS.add_steps(stage=stage,
                    steps=[f"equilibrate_protein_{i}" for i in config.ti_windows])
        STATUS.add_steps(stage=stage,
                    steps=[f"equilibrate_complex_{i}" for i in config.ti_windows])
        STATUS.update_step(stage=stage, step="setup", status="complete")

    if STATUS.get_status(stage=stage, step="mutate") != "complete":
        # cpptraj.to_pdb(structure_file=f"{md.jobs[-1].inputfile_name}.ncrst",
        #             parm_file=md.parm_file,
        #             pdb_name="equilibrated_complex.pdb",
        #             path=mutation_path)

        if os.path.isfile(os.path.join(mutation_setup_path,"equilibrated_complex.pdb" )) == False: # Mutation Case 1
            cpptraj.strip(key = f"!:1-{protein_max_resid}",
                structure_file=f"{md.jobs[-1].inputfile_name}.ncrst",
                parm_file=md.parm_file,
                output="equilibrated_complex.pdb",
                path=mutation_setup_path)
            cpptraj.extract_ligand(structure_file = f"{md.jobs[-1].inputfile_name}.ncrst",
                    parm_file = md.parm_file,
                    resid = protein_max_resid+1,
                    output_file="Ligand.mol2",
                    path = mutation_setup_path)
        else:
            assert os.path.isfile(os.path.join(mutation_setup_path,"Ligand.mol2")) ## Mutation case 2. File should already be copied. 
        equil_pdb = io.text_read(os.path.join(mutation_setup_path, "equilibrated_complex.pdb"))
        io.text_dump(text=pdb.mutate_residue(lines=equil_pdb,
                                    residue_number=config.mutation_resid,
                                    new_residue=config.mutation_residue, chain=""),
                            path=os.path.join(mutation_setup_path,"mutated_complex.pdb"))
        
        io.text_dump(leap.gen_leap_ti(ligand_name="Ligand",
                                    protein_1="equilibrated_complex.pdb",
                                    protein_2="mutated_complex.pdb",
                                    complex_out="complex_unmerged",
                                    protein_out="protein_unmerged",
                                    forcefield=config.forcefield,
                                    box=config.box), os.path.join(mutation_setup_path, "leap4ti.in"))
        leap.run_leap(path=mutation_setup_path, file="leap4ti.in")
        parmed.merge_ti(structure_file="complex_unmerged.rst7",
                        parm_file="complex_unmerged.parm7",
                        outfile="complex_merged",
                        protein_max=protein_max_resid,
                        mutant_res_id=config.mutation_resid,
                        path=mutation_setup_path,
                        parmed_file="complex_parmed.in")
        shutil.copy(os.path.join(mutation_setup_path, "complex_merged.rst7"),
                    os.path.join(mutation_complex_path, "complex_merged.rst7"),)
        shutil.copy(os.path.join(mutation_setup_path, "complex_merged.parm7"),
                    os.path.join(mutation_complex_path, "complex_merged.parm7"),)
        parmed.merge_ti(structure_file="protein_unmerged.rst7",
                        parm_file="protein_unmerged.parm7",
                        outfile="protein_merged",
                        protein_max=protein_max_resid,
                        mutant_res_id=config.mutation_resid,
                        path=mutation_setup_path,
                        parmed_file="protein_parmed.in")
        shutil.copy(os.path.join(mutation_setup_path, "protein_merged.rst7"),
                    os.path.join(mutation_protein_path, "protein_merged.rst7"),)
        shutil.copy(os.path.join(mutation_setup_path, "protein_merged.parm7"),
                    os.path.join(mutation_protein_path, "protein_merged.parm7"),)
        
        STATUS.update_step(stage=stage, step="mutate", status="complete")


    ti_protein = amber.Amber(start_coordinates="protein_merged.rst7",
                        parm_file="protein_merged.parm7")
    ti_protein.describe_structure(protein_residue_start=1,
            protein_residue_end=protein_max_resid+1, # Due to the extra residue in the merged file.
            )#TODO Add ligand and cofactor defenition.
    ti_protein.define_hardware(cpu = config.cpus, gpu = config.gpus)
    ti_protein.init_ti(scmask_1=f"':{config.mutation_resid}'",
                       timask_1=f"':{config.mutation_resid}'",
                       scmask_2=f"':{protein_max_resid+1}'",
                       timask_2=f"':{protein_max_resid+1}'")

    ti_complex = amber.Amber(start_coordinates="complex_merged.rst7",
                        parm_file="complex_merged.parm7")
    ti_complex.describe_structure(protein_residue_start=1,
            protein_residue_end=protein_max_resid+1, # Due to the extra residue in the merged file.
            )#TODO Add ligand and cofactor defenition.
    ti_complex.define_hardware(cpu = config.cpus, gpu = config.gpus)
    ti_complex.init_ti(scmask_1=f"':{config.mutation_resid}'",
                       timask_1=f"':{config.mutation_resid}'",
                       scmask_2=f"':{protein_max_resid+1}'",
                       timask_2=f"':{protein_max_resid+1}'")

    
    ti_protein = recipies.equil_ti(mm=ti_protein,
                                path=mutation_protein_path,
                                start_structure=ti_protein.start_coordinates,
                                lambda_value=0.5,
                                temperature=config.temperature)
    ti_complex = recipies.equil_ti(mm=ti_complex,
                                       path=mutation_complex_path,
                                       start_structure=ti_complex.start_coordinates,
                                       lambda_value=0.5,
                                       temperature=config.temperature)
    if STATUS.get_status(stage=stage, step="equilibrate_protein") != "complete":
        for job in ti_protein.jobs:
            print(job.run_path)
            job.exe(gpu=True)
        STATUS.update_step(stage=stage, step="equilibrate_protein", status="complete")

    if STATUS.get_status(stage=stage, step="equilibrate_complex") != "complete":
        for job in ti_complex.jobs:
            job.exe(gpu=True)
        STATUS.update_step(stage=stage, step="equilibrate_complex", status="complete")

    for structure in ["protein", "complex"]:
        if structure == "protein":
            mm = ti_protein
            path = mutation_protein_path
        elif structure == "complex":
            mm = ti_complex
            path = mutation_complex_path
        else:
            raise ValueError("Invalid structure type")
        # config.hpc.hpc.make_dir(os.path.join(hpc_path, path))

        complete: bool = False        
        for lam in config.ti_windows:
            window_path = os.path.join(path, str(lam))
            step = f"equilibrate_{structure}_{lam}"
            config.hpc.define_dirs(local_file_path=window_path, hpc_file_path=os.path.join(hpc_path, window_path))
            if STATUS.get_status(stage=stage, step=step) == "Not Started":
                complete=False
                io.make_dir(path=window_path)
                config.hpc.hpc.make_dir(hpc_work_dir=os.path.join(hpc_path, window_path))
                config.hpc.hpc.sync(work_dir=window_path, hpc_work_dir=os.path.join(hpc_path, window_path))
                
                shutil.copy(src=os.path.join(path, "ti_equil.ncrst"),
                        dst=os.path.join(window_path, "ti_equil.ncrst"))
                shutil.copy(src=os.path.join(path, f"{structure}_merged.parm7"),
                        dst=os.path.join(window_path, f"{structure}_merged.parm7"))
                
                mm = recipies.equil_ti(mm=mm, path=window_path,
                                        start_structure="ti_equil.ncrst",
                                        lambda_value=lam,
                                        temperature=config.temperature)
                slurm_id = None
                run_lines = []
                for job in mm.jobs[-4:]:
                    job.update_run_path(window_path)
                    # job.exe(hpc=config.hpc, dependency=slurm_id)
                    job.gen_input_file()
                    run_lines.append(job.gen_run_lines())
                print(run_lines)
                config.hpc.add_dependency(dependency=None)
                io.text_dump(text=config.hpc.gen_script(command=run_lines), path=os.path.join(window_path, config.hpc.file_name))
                config.hpc.submit()
                slurm_id = config.hpc.job.job_id

                # quit()

                # slurm_id = job.hpc.job.job_id

                print(f"INFO: equilibration of {structure}, lam={lam} submitted. ID = {slurm_id}")
                STATUS.update_step(stage=stage, step=step, status="submitted")
                STATUS.update_step(stage=stage, step = f"{step}_id",status=slurm_id)
            elif STATUS.get_status(stage=stage, step=step) == "submitted": 
                print("Job submitted to HPC")
                job_id = int(STATUS.get_status(stage=stage, step = f"{step}_id"))
                stat = config.hpc.hpc.check_slurm_status(slurm_id=job_id)
                print(f"INFO: Job {job_id} is {stat}.")
                if stat == "CD":
                    config.hpc.hpc.sync(work_dir=window_path, hpc_work_dir=os.path.join(hpc_path, window_path), direction="backward")
                    if lam == 1.0 and structure == "complex":
                        cpptraj.strip(key=f"!:1-{protein_max_resid+1}",structure_file=f"{mm.jobs[-1].outputfile_name}.ncrst", parm_file=mm.parm_file, output="equilibrated_mutant.pdb", path=window_path )
                        pdb_file = io.text_read(os.path.join(window_path, "equilibrated_mutant.pdb"))   
                        new_pdb = pdb.get_mutant_structure(pdb_file, config.mutation_resid, protein_max_resid+1)

                        io.text_dump(new_pdb, os.path.join(window_path, "equilibrated_mutant.pdb"))
                        io.text_dump(new_pdb, os.path.join(mutant_protein_path, f"equilibrated_mutant_{config.mutation_resid}_{config.mutation_residue}.pdb"))
                        cpptraj.extract_ligand(structure_file = f"{mm.jobs[-1].inputfile_name}.ncrst",
                                        parm_file = mm.parm_file,
                                        resid = protein_max_resid+2, # +2 because there is 2 of one residue in the TI file. 
                                        output_file="Ligand.mol2",
                                        path = window_path)
                        shutil.copy(src=os.path.join(window_path,"Ligand.mol2"),
                                    dst=os.path.join(mutant_protein_path,f"Ligand_{config.mutation_resid}_{config.mutation_residue}.mol2"))
                    STATUS.update_step(stage=stage, step=step, status="complete", )
                else:
                    complete=False
            prod_step = f"prod1_{structure}_{lam}"
            # STATUS.add_steps(stage=stage, steps=[prod_step])
            if STATUS.get_status(stage=stage, step=prod_step) == "Not Started":
                complete=False
                mm.set_ti(lam=lam, mbar=True, lambda_list=config.ti_windows)
                mm = recipies.prod_ti(mm=mm, path=window_path, start_structure="ti_equil.ncrst",temperature=config.temperature, outfile="prod1")
                if STATUS.get_status(stage=stage, step=step) == "submitted": 
                    mm.jobs[-1].exe(hpc=config.hpc, dependency=int(STATUS.get_status(stage=stage, step = f"{step}_id")))
                elif STATUS.get_status(stage=stage, step=step) == "complete":
                    mm.jobs[-1].exe(hpc=config.hpc, dependency=None)
                else:
                    break
                
                print(f"INFO: equilibration of {structure}, lam={lam} submitted. ID = {mm.jobs[-1].hpc.job.job_id}")
                STATUS.update_step(stage=stage, step=prod_step, status="submitted")
                STATUS.update_step(stage=stage, step = f"{prod_step}_id",status=mm.jobs[-1].hpc.job.job_id)

            elif STATUS.get_status(stage=stage, step=prod_step) == "submitted": 
                print("Job submitted to HPC")
                job_id = int(STATUS.get_status(stage=stage, step = f"{prod_step}_id"))
                stat = config.hpc.hpc.check_slurm_status(slurm_id=job_id)
                print(f"INFO: Job {job_id} is {stat}.")
                if stat == "CD":
                    config.hpc.hpc.sync(work_dir=window_path, hpc_work_dir=os.path.join(hpc_path, window_path), direction="backward")
                    STATUS.update_step(stage=stage, step=prod_step, status="complete" )
                else:
                    complete=False
        # if complete:
        #     if STATUS.get_status("")
        #     getdvdl_alchemlyb.get_dvdl_main(glob_pattern="prod1.en",
        #                                 path=path,
        #                                 windows=config.ti_windows)


if __name__ == "__main__":
    main()
