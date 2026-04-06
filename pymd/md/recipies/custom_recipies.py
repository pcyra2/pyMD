import os

import pymd.tools.convert as convert
from pymd.md.md import MDClass 


def qian_init_system(mm: MDClass, path: str) -> MDClass:
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
    mm.build(input_file_name="min1.in",
            input_structure="complex.rst7",
            output_file_name="min1.out",
            run_path=path,
            gpu=True)

    mm.set_minimisation(steps=10000, steps_steepest=5000)
    mm.set_outputs(energy=10,restart=500, trajectory=0)
    mm.build(input_file_name="min2.in",
            input_structure="min1.rst7",
            output_file_name="min2.out",
            run_path=path,
            gpu=True)

    mm.set_heating(total_steps=250000,
                start_temperature=0,
                end_temperature=318.15, 
                thermostat="langevin")
    mm.set_restraints(restraint="protein")
    mm.set_outputs(energy=100, restart=100, trajectory=100)
    mm.build(input_file_name="heat.in",
            input_structure="min2.rst7",
            output_file_name="heat.out",
            run_path=path,
            gpu=True)

    mm.set_nvt(steps=500000,
               temperature=318.15)
    mm.set_outputs(energy=1000, restart=1000, trajectory=10000)
    mm.set_restraints(restraint="protein")
    mm.build(input_file_name="NVT1.in",
            input_structure="heat.rst7",
            output_file_name="NVT1.out",
            run_path=path,
            gpu=True)



    mm.set_npt(steps=500000,
               temperature=318.15,
               barostat="monte_carlo")
    mm.set_restraints("backbone")
    mm.set_outputs(energy=1000, restart=1000, trajectory=10000)
    mm.build(input_file_name="NPT1.in",
            input_structure="NVT1.rst7",
            output_file_name="NPT1.out",
            run_path=path,
            gpu=True)
    

    mm.set_npt(steps=500000,
               temperature=318.15)
    mm.set_outputs(energy=1000, restart=1000, trajectory=10000)
    mm.build(input_file_name="NPT2.in",
            input_structure="NPT1.rst7",
            output_file_name="NPT2.out",
            run_path=path,
            gpu=True)

    mm.set_npt(steps=500000,
               temperature=318.15, pressure=1)
    mm.set_outputs(energy=1000, restart=1000, trajectory=10000)
    mm.build(input_file_name="NPT2.in",
            input_structure="NPT1.rst7",
            output_file_name="NPT2.out",
            run_path=path,
            gpu=True)

    return mm