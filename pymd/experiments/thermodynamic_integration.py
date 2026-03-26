"""
This script should automatically run thermodynamic integration.
"""
from  dataclasses import dataclass
import os

from pymd.md.recipies import thermodynamic_integration as TI
from pymd.md.recipies import standard_md
from pymd.tools import io
from pymd.md.md import MDClass
from pymd.tools.slurm import Slurm

@dataclass
class ConfigClass:
    """
    #TODO
    """
    input_file: str = "Job.conf"
    run_dir: str = "./"
    base_protein: str = ""
    base_ligand: str = ""
    change_type: str = "protein"
    mutation: str = ""
    pre_parameterised: bool = True
    pre_equilibrated: bool = False
    parm_file: str|None = None
    topology_file: str|None = None
    cpus: int = 12
    gpus: int = 1
    hpc: dict = dict(partition = "compchemq",
                    module_files = ["amber-uon/gcc11.3.0/24", "cuda-12.2.2"],
                    wall_time = 168)

    def __init__(self) -> None:
        pass

    def to_dict(self)->dict:
        """Returns a dictionary of the class attributes"""
        return {key:value for key, value in vars(self).items() if not key.startswith('_')}

    def from_dict(self, d: dict) -> None:
        """
        Initialises config from dictionary.

        Args:
            d (dict): dictionary containing input variables. 
        """
        for key, value in d.items():
            if key in vars(self).keys():
                setattr(self, key, value)
        assert self.change_type in TI.TI_TYPES, \
            f"TI mutation {self.change_type} is not known. Only accepts: {TI.TI_TYPES}"
        if self.pre_equilibrated is True:
            self.pre_parameterised = True
        if self.pre_parameterised is True:
            assert self.parm_file is not None, "ERR: Equilibrated parameter file is required."
            assert self.topology_file is not None, "ERR: Equilibrated topology file is required."


def main() -> None:
    """
    Runs TI.
    """
    config = ConfigClass()
    if os.path.isfile(path=config.input_file):
        c_data = io.json_read(path=config.input_file)
        config.from_dict(d=c_data)
        io.json_dump(data=config.to_dict(), path=config.input_file)

    if config.pre_parameterised is False:
        raise NotImplementedError

    md = MDClass(backend="AMBER")
    md.set_parmfile(parmfile=config.parm_file) # pyright: ignore[reportArgumentType]
    md.define_hardware(cpu = config.cpus, gpu = config.gpus)

    if config.pre_equilibrated is False:
        md = standard_md.initialise_system(mm=md, path="./setup")
        for job in md.jobs:
            # if job.gpu:
            #     partition = "compchemq"
            #     gpu=1
            # else: 
            #     partition = "defq"
            #     gpu=0
            # slurm_sub = Slurm(partition=partition)
            # slurm_sub.set_modules(config.hpc["module_files"])
            # slurm_sub.set_gpus(gpu)
            # slurm_sub.set_ntasks(job.kernel.cores)
            # slurm_sub.set_name(job.inputfile_name)
            job.exe()

if __name__ == "__main__":
    main()
