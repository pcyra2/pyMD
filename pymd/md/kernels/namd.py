
import subprocess
import os
import copy

from pymd.user_configs.namd_defaults import NamdConfig

class Namd:
    defaults: NamdConfig
    config: NamdConfig
    parm_file: str
    cores: str # either +pNCORES or +oneWthPerCore

    def __init__(self, config: NamdConfig = NamdConfig()) -> None:
        self.defaults = copy.deepcopy(x=config)
        self.config = copy.deepcopy(x=config)

    def _gen_runlines(self, 
            input_file_name: str,
            output_file_name: str|None = None,
            gpu: bool = False) -> str:
        if output_file_name is None:
            output_file_name = input_file_name
        if gpu:
            return f"{self.defaults._GPUPath} {self.cores} +setcpuaffinity +devices 0 {input_file_name}.in > {output_file_name}.log"
        else:
            return f"{self.defaults._GPUPath} {self.cores} +setcpuaffinity {input_file_name}.in > {output_file_name}.log"


    def set_global(
            self,
            parmfile: str) -> None:
        """
        Defines the parameter and coordinate files for the initial structure. 

        Args:
            param (str): .parm7 file
        """
        self.parm_file = parmfile
        self.config.parmfile = parmfile
        self.defaults.parmfile = parmfile

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

    def set_cores(self, cores: int) -> None:
        assert cores > 0, "ERROR: Number of cores must be greater than zero"
        #TODO implement checking to see if it is +oneWthPerCore
        self.cores = f"+p{cores}"

    
    def _reset_config(self) -> None:
        """Reset the configuration to defaults."""
        self.config = copy.deepcopy(x=self.defaults)