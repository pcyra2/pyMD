"""
#TODO
"""
import copy
import os
import time

from pymd.user_configs.amber_defaults import AmberConfig
from pymd.tools import convert, io
import pymd.md.utilities.leap as PyLeap
from pymd.tools.slurm import Slurm

class MDJobClass:
    """
    #TODO
    """
    inputfile: list[str]
    inputfile_name: str
    outputfile_name: str
    input_structure: str
    run_line: str|list[str]
    run_path: str
    complete: bool = False
    kernel: AmberConfig
    wall_time: float
    gpu: bool = False
    hpc: Slurm|None = None

    def __init__(self,
                inputfile_name: str,
                input_structure: str,
                outputfile_name:str,
                run_path: str = "./"
                ) -> None:
        """
        #TODO

        Args:
            inputfile_name (str): _description_
            input_structure (str): _description_
            outputfile_name (str): _description_
            run_path (str, optional): _description_. Defaults to "./".
        """
        self.inputfile_name = inputfile_name
        self.outputfile_name = outputfile_name
        self.complete = False
        self.input_structure = input_structure
        self.run_path = run_path


    def add_inputfile(self) -> None:
        """The inputfile as a list of lines
        """
        self.inputfile = self.kernel.gen_input_file(filename = self.inputfile_name)


    def add_kernel(self, config: AmberConfig) -> None:
        """Adds the kernel object to allow for direct running.

        Args:
            config (Amber): Amber Kernel object.
        """
        self.kernel = copy.deepcopy(x=config)


    def add_run_lines(self, lines: list[str]|str) -> None:
        """Adds run-lines to the job. Not really necessary currently as I have the job.exe 
            although could be useful later to save run-lines for slurm submission.

        Args:
            lines (list[str] | str): lines to run. Usually in a list of commands to parse to 
                subprocess
        """
        if isinstance(lines, str):
            lines = lines.split()
        self.run_line = lines


    def to_gpu(self) -> None:
        """Converts the job to a GPU job
        """
        self.gpu = True


    def to_cpu(self) -> None:
        """Swaps the job back to a CPU job
        """
        self.gpu = False


    def attach_slurm(self, hpc:Slurm) -> None:
        """
        #TODO

        Args:
            hpc (Slurm): _description_
        """
        self.hpc = hpc


    def exe(self, gpu: bool|None = None, hpc: Slurm|None = None) -> None:
        """
        #TODO

        Args:
            gpu (bool | None, optional): _description_. Defaults to None.
            hpc (Slurm | None, optional): _description_. Defaults to None.
        """
        if gpu is not None and gpu is True:
            self.to_gpu()
        elif gpu is not None and gpu is False:
            self.to_cpu()
        if hpc is not None:
            self.hpc = hpc
        cpu_path = self.kernel.get_exe_path(gpu=False)
        if self.gpu and self.hpc is None:
            gpu_path = self.kernel.get_exe_path(gpu=True)
            if gpu_path is not None:
                if gpu_path is None:
                    assert cpu_path is not None
                    self.to_cpu()
        elif self.hpc is None:
            assert cpu_path is not None

        self.run_line = self.kernel._gen_runlines(
                            input_file_name=self.inputfile_name,
                            input_structure_name=self.input_structure,
                            output_file_name=self.outputfile_name,
                            gpu=self.gpu)
        if self.hpc is not None:
            assert self.run_line == self.hpc.local_file_dir, \
                "ERR: There is a mis-match between the cwd of the slurm object and the md job."

            ## Generate slurm submission script
            slurm_script = self.hpc.gen_script(command=self.run_line)
            io.text_dump(text=slurm_script, path=os.path.join(self.run_path, self.hpc.file_name))

            ## Sync the files, submit, and wait for end.
            self.hpc.submit(wait_for_finish=True)

            ## Sync the files back
            self.hpc.hpc.sync(work_dir=self.run_path, hpc_work_dir=self.hpc.hpc_run_dir, direction="backward")
            if self.hpc.job.status == "completed":
                self.complete = True
            self.wall_time = self.hpc.job.wall_time
        else:
            start = time.perf_counter()
            output = self.kernel.exec(input_file_name=self.inputfile_name,
                            output_file_name=self.outputfile_name,
                            input_structure_name=self.input_structure,
                            path=self.run_path,
                            gpu=self.gpu)
            stop = time.perf_counter()
            self.complete = True
            self.wall_time = stop - start


class MDClass:
    """Class for handling the MD simulations. It contains job classes which can be used to handle 
    the input/output data. It also contains the MD package backend and other system configurations.

    Attributes:
        jobs (list[MDJobClass]): List of MDJobClass classes that contain the job information.
        current_job (MDJobClass): The MDJobClass that is currently being run/generated.
        num_CPU (int): The number of CPU cores to run calculations on. Defaults to 1.
        num_GPU (int): The number of GPU's available to the MD calculation. Defaults to 0.
        base_slurm (Slurm): A template SLURM Class so that jobs can interface with a HPC.
    """
    jobs: list[MDJobClass] = []
    latest_job: MDJobClass|None = None
    num_cpu: int = 1
    num_gpu: int = 0
    base_slurm: Slurm|None
    start_coordinates: str
    parm_file: str
    protein_start: int
    protein_end: int
    cofactors: list[int]|int
    ligands: list[int]|int

    def __init__(self,
            start_coordinates: str,
            parm_file: str
            ) -> None:
        self.start_coordinates = start_coordinates
        self.parm_file = parm_file
    

    def add_HPC(self, hpc: Slurm) -> None:
        """
        Adds a default SLRUM config that can be used to generate HPC interfaces

        Args:
            hpc (Slurm): The base SLURM config.
        """
        self.base_slurm = hpc


    def set_parmfile(
            self,
            parm_file: str
            ) -> None:
        """Sets the paramfile for the MD calculation.
        
        Args:
            parm_file (str): The name of the parmfile.
        """
        self.parm_file = parm_file


    def define_hardware(
            self,
            cpu: int = 1,
            gpu: int = 0 ) -> None:
        """Sets the CPU and GPU configuration for the calculation. 

        Args:
            cpu (int): The number of CPUs to give to the MD package.
                        Defaults to 0.
            gpu (int): The number of GPUs to give to the MD package.
                        Defaults to 0.
        """
        self.num_cpu = cpu
        self.num_gpu = gpu

    def describe_structure(self,
            protein_residue_start: int,
            protein_residue_end: int,
            cofactors: list[int]|int|None = None,
            ligands: list[int]|int|None = None) -> None:
        self.protein_start = protein_residue_start
        self.protein_end = protein_residue_end
        if cofactors is None:
            self.cofactors = cofactors
        if ligands is None:
            self.ligands = ligands
    
    def set_outputs(
            self,
            energy: int,
            restart: int,
            trajectory: int
            ) -> None:
        """Sets the output frequencies for the calculation. 

        Args:
            energy (int): how frequently to print the energy (and other associated values)
            restart (int): how frequently to update the restart coordinates
            trajectory (int): how frequently to write to the trajectory file
        """
        raise NotImplementedError("Function not implemented by kernel.")
    
    def set_restraints(self, restraint: str = "all_not_solvent", restraint_wt: float = 5.0) -> None:
        """
        Allows for simple restraints using ambers selection algebra

        Args:
            restraint (str): 
            restraint_wt (float, optional): Harmonic restraint weight. Defaults to 5.0.
        """
        raise NotImplementedError("Function not implemented by kernel.")
    
    def set_minimisation(self,
            steps: int,
            steps_steepest: int|None = None
            ) -> None:
        """Initialises standard minimisation parameters

        Args:
            steps (int): Total number of minimisation steps
            steps_steepest (int, optional): Number of steepest-descent gradient steps to perform
        """
        raise NotImplementedError("Function not implemented by kernel.")
    
    def set_heating(self,
                    total_steps: int,
                    start_temperature: float,
                    end_temperature: float,
                    heating_steps: int|None = None,
                    time_step: float = 2,
                    thermostat: str|int|None = None,
                    continue_dynamics: bool = False
                    ) -> None:
        """Initialises standard heating parameters for the calculaiton.

        Args:
            heating_steps (int): Number of steps to heat for.
            total_steps (int): Total number of steps in the simulation.
            start_temperature (float): Initial temperature to heat from.
            end_temperature (float): Temperature to heat to. 
            time_step (float): Time step for the dynamics in Femtosteps.
            thermostat (str|int|None): Thermostat to use for temperature control. 
                If none is provided, the default is used from the config.
            continue_dynamics (bool): Whether to read in velocities from a previous simulation.
        """
        raise NotImplementedError("Function not implemented by kernel.")
    
    def set_nvt(self,
                steps: int,
                temperature: float,
                thermostat: str|int|None = None,
                time_step: float = 2,
                continue_dynamics: bool = True
                ) -> None:
        """Sets up the variables required for an NVT simulation. 

        Args:
            steps (int): Number of MD steps to perform.
            temperature (float): The temperature to run the NVT ensemble at. 
            thermostat (str|int|None, optional): The thermostat to use. 
                Defaults to the default set in the default config.
            time_step (float): The timestep to use in femotoseconds. Defaults to 2 fs.
            continue_dynamics (bool): Whether to read in velocities from a previous simulation.
        """
        raise NotImplementedError("Function not implemented by kernel.")
    
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
        """Sets up the variables required for an NPT simulation. 

        Args:
            steps (int): Number of MD steps to perform.
            temperature (float): The temperature to run the NPT ensemble at.
            thermostat (str|int|None, optional): The thermostat to use. 
                Defaults to the default set in the default config.
            pressure (float|None): The pressure to run the NPT ensemble at. If None, it maintains
                current presure. Defaults to None.
            barostat (str|int|None, optional): The barostat to use. 
                Defaults to the default set in the default config.
            pressure_scaling (int|str|None): The pressure scaling to use. 
                If None, defaults to the config Defaults. 
            time_step (float): The timestep to use in femotoseconds. Defaults to 2 fs.
            continue_dynamics (bool): Whether to read in velocities from a previous simulation.
        """
        raise NotImplementedError("Function not implemented by kernel.")
    
    def _reset_config(self) -> None:
        """Reset the configuration to defaults."""
        raise NotImplementedError("Function not implemented by kernel.")
    
    def build(self,
            input_file_name: str,
            input_structure: str,
            output_file_name: str,
            run_path: str,
            gpu: bool = False,
            hpc: Slurm|None = None
            ) -> None:
        """Builds the config and converts into a Job with a kernel. 
        
        Args:
            input_file_name (str): The name of the input file.
            input_structure (str): The name of the input coordinate file. 
            output_file_name (str): The name of the output file. 
            run_path (str): The path to run the calculation. 
            gpu (bool): Whether to run the calculation on a GPU. 
            hpc (Slurm|None): Whether to assign a HPC object to the calculation. 
        """
        raise NotImplementedError("Function not implemented by kernel.")