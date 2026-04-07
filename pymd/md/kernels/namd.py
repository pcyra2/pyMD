"""
#TODO
"""
import copy

from pymd.md.md import MDClass, MDJobClass
from pymd.tools.slurm import Slurm
from pymd.user_configs.namd_defaults import NamdConfig
from pymd.tools import convert

class Namd(MDClass):
    defaults: NamdConfig
    config: NamdConfig

    def __init__(self,
            start_coordinates: str,
            parm_file: str,
            config: NamdConfig = NamdConfig(),
            amber_parm: bool = True) -> None:
        super().__init__(start_coordinates=start_coordinates, parm_file=parm_file)
        self.defaults = copy.deepcopy(x=config)
        self.config = copy.deepcopy(x=config)
        self.defaults.parmfile = parm_file
        self.config.parmfile = parm_file
        if amber_parm:
            self.config.ambercoor = start_coordinates
            self.defaults.ambercoor = start_coordinates

            self.config.amber = "yes"
            self.defaults.amber = "yes"
        self.config.seed = self.defaults.seed


    def set_outputs(
            self,
            energy: int,
            restart: int,
            trajectory: int) -> None:
        """Sets the output frequencies for the calculation. 

        Args:
            energy (int): how frequently to print the energy (and other associated values)
            restart (int): how frequently to update the restart coordinates
            trajectory (int): how frequently to write to the trajectory file
        """
        self.config.set_outputs(restart=restart, energy=energy, trajectory=trajectory)


    def set_restraints(self,
            restraint: str = "all_not_solvent",
            restraint_wt: float = 5) -> None:
        pass


    def set_minimisation(self, steps: int,
            steps_steepest: int|None = None
            ) -> None:
        self.config.set_minimisation_variables(steps_total=steps)
        self.config.clear_attribute(attribute="run")


    def set_heating(self,
            total_steps: int,
            start_temperature: float,
            end_temperature: float,
            heating_steps: int|None = None,
            time_step: float = 2,
            thermostat: str|int|None = None,
            continue_dynamics: bool = False) -> None:
        pass


    def set_nvt(self, steps: int,
            temperature: float,
            thermostat: str|int|None = None,
            time_step: float = 2,
            continue_dynamics: bool = True
            ) -> None:
        pass


    def set_npt(self,
            steps: int,
            temperature: float,
            thermostat: str|int|None = None,
            pressure: float|None = None,
            barostat: str|int|None = None,
            pressure_scaling: int|str|None = None,
            time_step: float = 2,
            continue_dynamics: bool = True
            ) -> None:
        pass


    def _reset_config(self) -> None:
        """Reset the configuration to defaults."""
        self.config = copy.deepcopy(x=self.defaults)


    def build(self,
            input_file_name: str,
            input_structure: str,
            output_file_name: str,
            run_path: str,
            gpu: bool = False,
            hpc: Slurm|None = None
            ) -> None:
        self.latest_job = MDJobClass(inputfile_name = input_file_name,
                input_structure = input_structure,
                outputfile_name = output_file_name,
                run_path = run_path)
        if gpu:
            self.latest_job.to_gpu()
        if hpc is not None:
            self.add_HPC(hpc)
        self.jobs.append(self.latest_job)
        self._reset_config()
