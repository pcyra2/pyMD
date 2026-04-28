import os
import time
# from pymd.experiments.md.replica_md.experiment import config
from pymd.md.utilities import antechamber, leap
from pymd.tools import slurm, pdb, io, convert, structure
from pymd.tools.status_tracker import StatusTracker
from pymd.md.kernels.amber import Amber

def init_hpc(config) -> slurm.Slurm:
    hpc = slurm.Slurm(partition=config.hpc_partition)
    hpc.set_gpus(gpus=config.gpus)
    hpc.set_ntasks(tasks=config.cpus)
    hpc.set_mem(mem=config.memory)
    hpc.set_modules(modules=config.hpc_modules)
    hpc.set_time(wall_time=168)
    return hpc

def init_status(config) -> StatusTracker:
    STATUS = StatusTracker(file_path =  config.status_file)
    if os.path.isfile(path=config.status_file):
        print(f"INFO: Reading job status from {config.status_file}")
        STATUS.from_dict()
    return STATUS

def gen_lig_parms(config, hpc_path: str, STATUS: StatusTracker) -> None:
	ligand = structure.Molecule(Name=config.ligand_code)
	file = io.text_read(os.path.join("Setup", config.ligand_file))
	if config.ligand_file.endswith(".xyz"):
		ligand.from_xyz(file, charge=config.lig_charge_spin[0], spin=config.lig_charge_spin[1])
	elif config.ligand_file.endswith(".mol2"):
		ligand.from_mol2(file, charge=config.lig_charge_spin[0], spin=config.lig_charge_spin[1])

	gauss_inp =  antechamber.gen_gaussian_for_antechamber(ligand, proc=config.cpus, mem=config.memory)
	gaus_hpc = slurm.Slurm(partition="defq")
	gaus_hpc.set_gpus(0)
	gaus_hpc.set_ntasks(config.cpus)
	gaus_hpc.set_mem(mem=config.memory)
	gaus_hpc.set_time(wall_time=168)
	gaus_hpc.set_modules(modules=["gaussian-uon/avx2/g16"])
	gaus_hpc.define_dirs(local_file_path="Setup", hpc_file_path=os.path.join(hpc_path, "Setup"))
	
	if STATUS.get_status("parameterisation", "lig_prep") != "submitted":
		gaus_hpc.hpc.make_dir(gaus_hpc.hpc_run_dir)
		io.text_dump(gauss_inp, os.path.join("Setup", f"{config.ligand_code}.gin"))
		slurm_sub = gaus_hpc.gen_script(command=f"g16 {config.ligand_code}.gin")
		io.text_dump(slurm_sub, os.path.join("Setup", gaus_hpc.file_name))
		# quit()
		gaus_hpc.submit()
		STATUS.update_step("parameterisation", "lig_prep", "submitted")
		STATUS.update_step("parameterisation", "lig_prep_id", gaus_hpc.job.job_id)
		time.sleep(30)
	job_id = int(STATUS.get_status("parameterisation", "lig_prep_id"))
	while gaus_hpc.hpc.check_slurm_status(slurm_id=job_id) != "CD":
		print(f"INFO: Waiting for Gaussian job {job_id} to finish...")
		time.sleep(30)
	print("TMP")
	gaus_hpc.hpc.sync(work_dir=gaus_hpc.local_file_dir, hpc_work_dir=gaus_hpc.hpc_run_dir, direction="reverse")
	antechamber.run_antechamber(path="Setup", lig_code=config.ligand_code, charge=config.lig_charge_spin[0], mult=config.lig_charge_spin[1]+1)
	STATUS.update_step("parameterisation", "lig_prep", "complete")

def run_leap(config, STATUS: StatusTracker) -> None:

	leap_file = leap.gen_leap(config.protein_file, ligand_name=config.ligand_code, waters=config.waters_file, ions=config.ions_file, parm_file=config.parmfile, amber_coor=config.start_structure, forcefield="ff14SB", gaff="gaff2")
	io.text_dump(leap_file, os.path.join("Setup", "leap.in"))
	leap.run_leap(path="Setup", file="leap.in")
	if leap.check_leap_log("Setup") == False:
		print("ERROR: Leap failed, check the log file for details.")
		STATUS.update_step("parameterisation", "leap", "ERROR")
	return STATUS

def init_md(config) -> Amber:
    md = Amber(start_coordinates=config.start_structure,
                   parm_file=config.parmfile)

    protein_max_id: int = pdb.get_protein_res_id_range(lines=io.text_read(path=config.base_pdb))
    print(protein_max_id)
    md.describe_structure(protein_residue_start=1,
                          protein_residue_end=protein_max_id)

    md.define_hardware(cpu=config.cpus, gpu = config.gpus)
    return md

def pre_prod(md: Amber, config, run_dir: str) -> Amber:
    md.set_minimisation(10000, 3000)
    md.set_restraints("protein")
    md.set_outputs(energy=1, restart=100, trajectory=0)
    md.build(input_file_name="min1", 
            input_structure = config.start_structure,
            output_file_name = "min1",
            run_path = run_dir,
            gpu=True)

    md.set_minimisation(80000, 30000)
    md.set_outputs(energy=1, restart=100, trajectory=0)
    md.build(input_file_name="min2", 
            input_structure = "min1.ncrst",
            output_file_name = "min2",
            run_path = run_dir,
            gpu=True)
    
    md.set_minimisation(50000, 2000)
    md.set_outputs(energy=1, restart=100, trajectory=0)
    md.build(input_file_name="min3", 
            input_structure = "min2.ncrst",
            output_file_name = "min3",
            run_path = run_dir,
            gpu=True)

    heat_steps = convert.time_to_steps(sim_time=50, time_units="ps", timestep=0.002)
    md.set_heating(heating_steps=int(0.9*heat_steps),
            total_steps=heat_steps,
            start_temperature=0,
            end_temperature=config.temperature)
    md.set_outputs(energy=1, restart=100, trajectory=int(heat_steps/10))
    md.build(input_file_name="heat", 
            input_structure = "min3.ncrst",
            output_file_name = "heat",
            run_path = run_dir,
            gpu=True)

    nvt_steps = convert.time_to_steps(sim_time=100, time_units="ps", timestep=0.002)
    md.set_nvt(steps=nvt_steps,
            temperature=config.temperature)
    md.set_outputs(energy=10, restart=100, trajectory=int(nvt_steps/100))
    md.build(input_file_name="NVT1",
            input_structure="heat.ncrst",
            output_file_name="NVT1",
            run_path=run_dir,
            gpu=True)

    nvt_steps = convert.time_to_steps(sim_time=1, time_units="ns", timestep=0.002)
    md.set_npt(steps=nvt_steps,
            temperature=config.temperature,
            pressure = 1)
    md.set_outputs(energy=10, restart=100, trajectory=int(nvt_steps/100))
    md.build(input_file_name="NPT1",
            input_structure="NVT1.ncrst",
            output_file_name="NPT1",
            run_path=run_dir,
            gpu=True)

    nvt_steps = convert.time_to_steps(sim_time=100, time_units="ns", timestep=0.002)
    md.set_npt(steps=nvt_steps,
            temperature=config.temperature,
            pressure = 1)
    md.set_outputs(energy=100, restart=100, trajectory=int(nvt_steps/200))
    md.build(input_file_name="NPT2",
            input_structure="NPT1.ncrst",
            output_file_name="NPT2",
            run_path=run_dir,
            gpu=True)

    return md


def production(md: Amber,
        STATUS: StatusTracker,
            config,
            name: str,
            hpc: slurm.Slurm,
            start_structure: str,
            run_dir: str) -> tuple[Amber, StatusTracker]:
	if STATUS.get_status("production", name) != "complete":
		steps = convert.time_to_steps(sim_time=config.production_time, time_units="ns", timestep=0.002)
		md.set_npt(steps=steps,
            temperature=config.temperature,
            pressure = 1)
		md.set_outputs(energy=100, restart=100, trajectory=int(steps/200))
		md.build(input_file_name=name,
                input_structure=start_structure,
                output_file_name=name,
                run_path=run_dir,
                gpu=True)
		if STATUS.get_status("production", name) == "submitted":
			job_id = int(STATUS.get_status("production", f"{name}_id"))
			stat = hpc.hpc.check_slurm_status(slurm_id=job_id)
			print(f"INFO: Job {job_id} is {stat}.")
			if stat == "CD":
				hpc.hpc.sync(work_dir=hpc.local_file_dir, hpc_work_dir=hpc.hpc_run_dir, direction="reverse")
				md.jobs[-1].add_analysis_lines(outfile_analysis_lines=["Etot", "TEMP(K)", "VOLUME", "PRESS", "Density"], trajectory_analysis_lines=[])
				md.analyse(job_int=-1, save_data=True, plot_fig=True, save_fig=True)
				STATUS.update_step(stage="production", step=name, status="complete" )
		else:
			md.jobs[-1].exe(hpc=hpc)
			STATUS.update_step(stage="production", step=name, status="submitted" )
			STATUS.update_step(stage="production", step=f"{name}_id", status=md.jobs[-1].hpc.job.job_id)
			# stat = "PD"
			# while stat == "PD":
			# 	time.sleep(20)
			# 	stat = hpc.hpc.check_slurm_status(slurm_id=int(md.jobs[-1].hpc.job.job_id))
	return md, STATUS
    