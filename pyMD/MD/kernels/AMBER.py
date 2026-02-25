from pyMD.UserConfigs.AmberDefaults import AmberConfig, THERMOSTATS, BAROSTATS, PRESSURE_SCALING

import subprocess

class Amber:
    defaults:AmberConfig = AmberConfig()
    parmfile:str
    cores:int

    def __init__(self, config: AmberConfig = AmberConfig()):
        self.config = config
    
    def _gen_runlines(self, input:str, output:str, gpu:bool = False):
        if gpu:
            return f"pmemd.cuda -O -i {output}.in -c {input} -r {self.parmfile} -o {output}.out -r {output}.rst7 -x {output}.nc"
        else:
            return f"sander -O -i {output}.in -c {input} -r {self.parmfile} -o {output}.out -r {output}.rst7 -x {output}.nc"

    def exec(self, input:str, output:str, gpu:bool=False, path:str = "./"):
        """
        Runs the amber software as part of the script.

        Args:
            input (str): Base name of input file
            output (str): Base name of output files
            gpu (bool): Whether to use GPU or not. Defaults to False
            path (str): Where to run the calculation. Defaults to ./

        Returns:
            outlines (str): The CLI output from runnning the command.
        """
        
        command = self._gen_runlines(input, output, gpu)
            
        print(f"INFO: Running command: {command}")
        with open(output, "w") as f:
            outlines = subprocess.run([command],stdout=f, cwd=path)
        return outlines

    def set_global(self, parmfile:str):
        """
        Defines the parameter and coordinate files for the initial structure. 

        Args:
            param (str): .parm7 file
        """
        self.parmfile = parmfile

    def set_outputs(self, energy:int, restart:int,  trajectory:int):
        """Sets the output frequencies for the calculation. 

        Args:
            energy (int): how frequently to print the energy (and other associated values)
            restart (int): how frequently to update the restart coordinates
            trajectory (int): how frequently to write to the trajectory file
        """
        self.config.set_outputs(restart=restart, energy=energy, trajectory=trajectory)

    def set_cores(self, cores:int):
        """Sets the number of cores to use for the MD simulation

        Args:
            cores (int): number of CPU's to run on
        """
        assert cores > 0, "Cannot have a negative number of CPU's"
        self.cores = cores

    def set_restraints(self, restraint_mask:str, restraint_wt:float = 5.0):
        """
        Allows for simple restraints using ambers selection algebra

        Args:
            restraint_mask (str): Atom selection
            restraint_wt (float, optional): Harmonic restraint weight. Defaults to 5.0.
        """
        
