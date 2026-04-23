import os

import pymd.tools.convert as convert
from pymd.md.md import MDClass 

def qian_init_system(mm: MDClass, path: str, start_structure: str, temperature: float ) -> MDClass:
	"""
    Args:
        mm (Amber, Namd): The MDClass object that contains the system information.

            Returns:
        MDClass: The MD Class object with the jobs generated.
	"""
	assert os.path.exists(path=path), f"Path {path} does not exist"
	mm.set_minimisation(steps=10000, steps_steepest=5000)
	mm.set_restraints(restraint = "protein")
	mm.set_outputs(energy=10,restart=500, trajectory=0)
	mm.build(input_file_name="min1",
    		input_structure=start_structure,
			output_file_name="min1",
			run_path=path,
			gpu=True)

	mm.set_minimisation(steps=10000, steps_steepest=5000)
	mm.set_outputs(energy=10,restart=500, trajectory=0)
	mm.build(input_file_name="min2",
            input_structure="min1.ncrst",
            output_file_name="min2",
            run_path=path,
            gpu=True)

	mm.set_heating(total_steps=250000,
                start_temperature=0,
                end_temperature=temperature, 
                thermostat="langevin")
	mm.set_restraints(restraint="protein")
	mm.set_outputs(energy=100, restart=100, trajectory=100)
	mm.build(input_file_name="heat",
            input_structure="min2.ncrst",
            output_file_name="heat",
            run_path=path,
            gpu=True)

	mm.set_nvt(steps=500000,
               temperature=temperature)
	mm.set_outputs(energy=1000, restart=1000, trajectory=10000)
	mm.set_restraints(restraint="protein")
	mm.build(input_file_name="NVT1",
            input_structure="heat.ncrst",
            output_file_name="NVT1",
            run_path=path,
            gpu=True)



	mm.set_npt(steps=500000,
               temperature=temperature,
               barostat="monte_carlo",
               pressure=1)
	mm.set_restraints(restraint="backbone")
	mm.set_outputs(energy=1000, restart=1000, trajectory=10000)
	mm.build(input_file_name="NPT1",
            input_structure="NVT1.ncrst",
            output_file_name="NPT1",
            run_path=path,
            gpu=True)
    
    

	mm.set_npt(steps=500000,
               temperature=temperature,
               pressure=1)
	mm.set_outputs(energy=1000, restart=1000, trajectory=10000)
	mm.build(input_file_name="NPT2",
            input_structure="NPT1.ncrst",
            output_file_name="NPT2",
            run_path=path,
            gpu=True)
	return mm

def equil_ti(mm: MDClass, path: str, start_structure:str, lambda_value: float, temperature: float) -> MDClass:
	mm.set_minimisation(steps=10000, steps_steepest=5000)
	mm.set_outputs(energy=10, restart=0, trajectory=0)
	mm.set_ti(lam=lambda_value, mbar=False)
	mm.config.set_vlim(20)
	mm.build(input_file_name="ti_min",
            input_structure=start_structure,
            output_file_name="ti_min",
            run_path=path,
            gpu=True)


	steps = convert.time_to_steps(sim_time=0.1, time_units="ns", timestep=0.002)
	mm.set_heating(total_steps=steps,
				start_temperature=0,	
				end_temperature=temperature,
                thermostat="langevin"
               	)
	mm.set_outputs(energy=1000, restart=1000, trajectory=int(steps/10))
	mm.set_ti(lam=lambda_value, mbar=False)
	mm.config.set_vlim(20)
	mm.build(input_file_name="ti_heat",
            input_structure="ti_min.ncrst",
            output_file_name="ti_heat",
            run_path=path,
            gpu=True)

	steps = convert.time_to_steps(sim_time=0.1, time_units="ns", timestep=0.002)
	mm.set_nvt(steps=steps,
               temperature=temperature,
               )
	mm.set_outputs(energy=1000, restart=1000, trajectory=int(steps/50))
	mm.set_ti(lam=lambda_value, mbar=False)
	mm.config.set_vlim(20)
	mm.build(input_file_name="ti_nvt",
            input_structure="ti_heat.ncrst",
            output_file_name="ti_nvt",
            run_path=path,
            gpu=True)
    
	steps = convert.time_to_steps(sim_time=1, time_units="ns", timestep=0.002)
	mm.set_npt(steps=steps,
               barostat="monte_carlo",
               temperature=temperature,
               pressure=1)
	mm.set_outputs(energy=1000, restart=1000, trajectory=int(steps/50))
	mm.set_ti(lam=lambda_value, mbar=False)
	mm.config.set_vlim(20)
	mm.build(input_file_name="ti_equil",
            input_structure="ti_nvt.ncrst",
            output_file_name="ti_equil",
            run_path=path,
            gpu=True)
	return mm

def prod_ti(mm: MDClass, path: str, start_structure:str,temperature: float, outfile: str = "ti_prod", ) -> MDClass:
    mm.set_npt(steps=convert.time_to_steps(sim_time=10, time_units="ns", timestep=0.002),
               temperature=temperature,
               pressure=1)
    mm.set_outputs(energy=100, restart=100, trajectory=50000)
    mm.build(input_file_name=outfile,
            input_structure=start_structure,
            output_file_name=outfile,
            run_path=path,
            gpu=True)
    return mm