"""
This script should automatically run thermodynamic integration.
"""
from  dataclasses import dataclass
import os
import shutil

from pymd.md.recipies import thermodynamic_integration as TI
from pymd.md.recipies import standard_md
from pymd.md.utilities import leap
from pymd.tools import io
from pymd.md.md import MDClass
from pymd.tools.slurm import Slurm

# @dataclass
class ConfigClass:
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
    input_data_dir: str = "./input_data"
    run_dir: str = "./"
    base_protein: str = ""
    base_ligand: str = ""
    mutation: str = ""
    mutation_resid: int = 0
    forcefield: str = "ff19SB"
    box: int = 10
    cpus: int = 12
    gpus: int = 1
    hpc: dict = dict(partition = "compchemq",
                    module_files = ["amber-uon/gcc11.3.0/24", "cuda-12.2.2"],
                    wall_time = 168)

    def __init__(self) -> None:
        self.input_file = self.input_file
        self.input_data_dir = self.input_data_dir
        self.run_dir = self.run_dir
        self.base_protein = self.base_protein
        self.base_ligand = self.base_ligand
        self.mutation = self.mutation
        self.mutation_resid = self.mutation_resid
        self.forcefield = self.forcefield
        self.box = self.box
        self.cpus = self.cpus
        self.gpus = self.gpus
        self.hpc = self.hpc

    def to_dict(self)->dict:
        """Returns a dictionary of the class attributes"""
        return {key:value for key, value in vars(self).items()}

    def from_dict(self, d: dict) -> None:
        """
        Initialises config from dictionary.

        Args:
            d (dict): dictionary containing input variables. 
        """
        for key, value in d.items():
            if key in vars(self).keys():
                setattr(self, key, value)


def main() -> None:
    """
    Runs TI.
    """
    config = ConfigClass()
    if os.path.isfile(path=config.input_file):
        c_data = io.json_read(path=config.input_file)
        config.from_dict(d=c_data)
    io.json_dump(data=config.to_dict(), path=config.input_file)

    assert os.path.isdir(config.input_data_dir)
    ## Setup the system
    setup_path = os.path.join(config.run_dir, "setup")
    io.make_dir(path=setup_path)

    shutil.copy(os.path.join(config.input_data_dir, config.base_protein), 
                os.path.join(setup_path, config.base_protein))
    shutil.copy(os.path.join(config.input_data_dir, config.base_ligand), 
                os.path.join(setup_path, config.base_ligand))
    shutil.copy(os.path.join(config.input_data_dir, config.base_ligand.replace("mol2", "frcmod")), 
                os.path.join(setup_path, config.base_ligand.replace("mol2", "frcmod")))
    
    leap_in = leap.gen_leap(ligand_name="Ligand", pdb_file="Protein", forcefield=config.forcefield)

    io.text_dump(text=leap_in, path=os.path.join(setup_path, "leap.in"))
    leap.run_leap(path=setup_path)


    # if config.pre_parameterised is False:
    #     raise NotImplementedError



    # md = MDClass(backend="AMBER")
    # md.set_parmfile(parmfile=config.parm_file) # pyright: ignore[reportArgumentType]
    # md.define_hardware(cpu = config.cpus, gpu = config.gpus)

    # if config.pre_equilibrated is False:
    #     md = standard_md.initialise_system(mm=md, path="./setup")
    #     for job in md.jobs:
    #         if job.gpu:
    #             partition = "compchemq"
    #             gpu=1
    #         else:
    #             partition = "defq"
    #             gpu=0
    #         slurm_sub = Slurm(partition=partition)
    #         slurm_sub.set_modules(config.hpc["module_files"])
    #         slurm_sub.set_gpus(gpu)
    #         slurm_sub.set_ntasks(job.kernel.cores)
    #         slurm_sub.set_name(job.inputfile_name)
    #         job.exe()



if __name__ == "__main__":
    main()
