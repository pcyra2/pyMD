"""
#TODO
"""
import copy
import os
from pymd.md.kernels.universal import MDJobClass
from pymd.md.kernels.amber import Amber
from pymd.user_configs.amber_defaults import AmberConfig
from pymd.tools import convert
import pymd.md.utilities.leap as PyLeap
from pymd.tools.slurm import Slurm


class MDClass:
    """Class for handling the MD simulations. It contains job classes which can be used to handle 
    the input/output data. It also contains the MD package backend and other system configurations.

    Attributes:
        base_config (AmberConfig): The default configuration for the MD package.
        _backend (str): The backend for the MD package.
        kernel (Amber): The MD package backend. #TODO This will be expanded as other 
                        backends are introduced.
        jobs (list[MDJobClass]): List of MDJobClass classes that contain the job information.
        current_job (MDJobClass): The MDJobClass that is currently being run/generated.
        num_CPU (int): The number of CPU cores to run calculations on. Defaults to 1.
        num_GPU (int): The number of GPU's available to the MD calculation. Defaults to 0.
        base_slurm (Slurm): #TODO
    """
    base_config: AmberConfig
    _backend: str
    kernel: Amber
    jobs: list[MDJobClass]
    current_job: MDJobClass
    num_cpu: int = 1
    num_gpu: int = 0
    base_slurm: Slurm|None


    def __init__(
            self,
            backend: str = "",
            config: AmberConfig = AmberConfig()
            ):
        self._backend = backend.casefold()
        self.base_config = config

        if self._backend == "amber":
            self.kernel = Amber(config)
        else:
            raise NotImplementedError(f"ERROR: Backend {self._backend} not implemented yet,"+ \
                                      " only AMBER is currently supported")
        self.jobs = []


    def add_HPC(self, HPC: Slurm):
        """
        #TODO

        Args:
            HPC (Slurm): _description_
        """
        self.base_slurm = HPC

    def set_parmfile(
            self,
            parmfile: str
            ):
        """Sets the paramfile for the MD calculation.
        
        Args:
            parmfile (str): The name of the parmfile.
        """
        self.kernel.set_global(parmfile)


    def define_hardware(
            self,
            cpu: int=1,
            gpu:int = 0 ):
        """Sets the CPU and GPU configuration for the calculation. 

        Args:
            cpu (int): The number of CPUs to give to the MD package.
                        Defaults to 0.
            gpu (int): The number of GPUs to give to the MD package.
                        Defaults to 0.
        """
        self.num_cpu=cpu
        self.num_gpu=gpu


    def make_job(self,
                input_file_name: str,
                input_structure: str,
                output_file_name: str,
                run_path: str ):
        """A workflow to build the MDJobClass correctly. 

        Args:
            input_file_name (str): The name of the inputfile, excluding the file extention.
            input_structure (str): The name of the input coordinate/topology file. This should
            include the file extention.
            output_file_name (str): The name of the outputfile, excluding the file extention.
            run_path (str): Where to run the calculation.
        """
        self.kernel.config.set_calculation_variables(self.kernel.parm_file,
                                                    input_coordinates=input_structure,
                                                    input_file_name=input_file_name,
                                                    output_file_name=output_file_name)

        self.current_job = MDJobClass(inputfile_name=input_file_name,
                                        input_structure=input_structure,
                                        outputfile_name=output_file_name,
                                        run_path=run_path)
        file = self.kernel.config.gen_input_file(input_file_name)
        self.current_job.add_inputfile(file)
        self.current_job.add_kernel(self.kernel)


    def minimize(self,
                input_structure: str,
                job_name: str,
                steps: int,
                restraints: str|None = None,
                run_path: str = "./",
                steps_steepest: int|None = None,
                traj_out: int = 10,
                restart_out: int = 10,
                energy_out: int = 10,
                hpc_sub: bool = False):
        """Sets up a minimisation job with the given parameters and adds it to the list of 
        jobs to be executed.

        Args:
            input_structure (str): Name of the input structure file (e.g. .rst7 for AMBER).
            job_name (str): Name of the job, used for naming input and output files.
            steps (int): Number of steps to run the minimisation for.
            restraints (str, optional): Selection algebra for restraints. Defaults to "".
            run_path (str, optional): Path where the job will be executed. Defaults to "./".
            steps_steepest (int, optional): Number of steepest descent minimization steps. 
                                            Defaults to 0.
            traj_out (int, optional): Frequency of trajectory output. Defaults to 10.
            restart_out (int, optional): Frequency of restart output. Defaults to 10.
            energy_out (int, optional): Frequency of energy output. Defaults to 10.
            hpc_sub (bool): #TODO
        """
        self.kernel.set_ensemble(ensemble="min", steps=steps, steps_steepest=steps_steepest)
        self.kernel.set_restraints(restraints, self.kernel.config.restraint_wt)

        self.kernel.set_outputs(energy_out, restart_out, traj_out)

        self.make_job(input_file_name=job_name,
                    input_structure=input_structure,
                    output_file_name=job_name,
                    run_path=run_path,
                    )

        if hpc_sub:
            if self.base_slurm is None:
                self.base_slurm = Slurm()
            slurm_sub = copy.deepcopy(self.base_slurm)
            slurm_sub.set_gpus(0)
            slurm_sub.define_dirs(run_path, os.path.join(slurm_sub.hpc_run_dir, run_path))
            slurm_sub.set_name(job_name)
            slurm_sub.set_ntasks(self.num_cpu)
            for module in slurm_sub.modules:
                if "cuda" in module:
                    slurm_sub.modules.remove(module)
            self.current_job.attach_slurm(slurm_sub)

        self.jobs.append(self.current_job)

    def heat(self,
            input_structure: str,
            job_name: str,
            steps: int,
            start_temperature: float = 0,
            end_temperature: float = 300,
            restraints: str|None = None,
            timestep: float = convert.time(2, in_unit="fs", out_unit="ps"),
            thermostat: str|int|None = None,
            traj_out: int = 100,
            energy_out: int = 10,
            restart_out: int = 10,
            path: str = "./",
            hpc_sub: bool = False):
        """Performs a standard heating workflow on the system

        Args:
            input_structure (str): Coordinates to heat
            job_name (str): Name of job
            steps (int): Number of steps
            start_temperature (float, optional): Initial temperature. Defaults to 0.
            end_temperature (float, optional): End temperature. Defaults to 300.
            restraints (str | None, optional): Any restraints to apply to the system. 
            Defaults to None.
            timestep (float, optional): timestep for dynamics in picoseconds. 
            Defaults to 0.002 ps (2 fs).
            thermostat (str | None, optional): Desired thermostat. 
            Defaults to the kernel's default thermostat.
            traj_out (int, optional): frequency to update trajectory. Defaults to 100.
            energy_out (int, optional): Frequency to print energy. Defaults to 10.
            restart_out (int, optional): Frequency to update restart structure. Defaults to 10.
            path (str, optional): _description_. Defaults to "./".
            hpc_sub (bool, optional): #TODO
        """
        if thermostat is None:
            thermostat = self.kernel.defaults.ntt
        self.kernel.set_ensemble(ensemble = "heat",
                                steps=steps,
                                thermostat = thermostat,
                                start_temp = start_temperature,
                                end_temperature = end_temperature,
                                timestep = timestep
                                )
        if restraints is not None:
            self.kernel.set_restraints(restraints)
        self.kernel.set_outputs(energy_out, restart_out, traj_out)

        self.make_job(input_file_name=job_name,
                    output_file_name=job_name,
                    input_structure=input_structure,
                    run_path=path)
        self.current_job.to_gpu()
        if hpc_sub:
            if self.base_slurm is None:
                self.base_slurm = Slurm()
            slurm_sub = copy.deepcopy(self.base_slurm)
            slurm_sub.set_gpus(1)
            slurm_sub.define_dirs(path, os.path.join(slurm_sub.hpc_run_dir, path))
            slurm_sub.set_name(job_name)
            slurm_sub.set_ntasks(self.num_cpu)
            self.current_job.attach_slurm(slurm_sub)

        self.jobs.append(self.current_job)


    def constant(self,
            input_structure: str,
            job_name: str,
            steps: int,
            temperature: float = 300.0,
            thermostat: str|int|None = None,
            pressure: float|None = None,
            barostat: str|int|None = None,
            restraints: str|None = None,
            timestep: float = convert.time(2, in_unit="fs", out_unit="ps"),
            path: str = "./",
            traj_out: int = 100,
            energy_out: int = 10,
            restart_out: int = 10,
            hpc_sub: bool = False
            ):
        """
        #TODO

        Args:
            input_structure (str): _description_
            job_name (str): _description_
            steps (int): _description_
            temperature (float, optional): _description_. Defaults to 300.0.
            thermostat (str | int | None, optional): _description_. Defaults to None.
            pressure (float | None, optional): _description_. Defaults to None.
            barostat (str | int | None, optional): _description_. Defaults to None.
            restraints (str | None, optional): _description_. Defaults to None.
            timestep (float, optional): _description_. 
                Defaults to convert.time(2, in_unit="fs", out_unit="ps").
            path (str, optional): _description_. Defaults to "./".
            traj_out (int, optional): _description_. Defaults to 100.
            energy_out (int, optional): _description_. Defaults to 10.
            restart_out (int, optional): _description_. Defaults to 10.
            hpc_sub (bool, optional): #TODO
        """
        if pressure is not None:
            ensemble = "npt"
            if barostat is None:
                barostat = self.kernel.defaults.barostat
        else:
            ensemble = "nvt"

        self.kernel.set_ensemble(ensemble = ensemble,
                                steps=steps,
                                temperature = temperature,
                                thermostat = thermostat,
                                pressure = pressure,
                                barostat = barostat,
                                timestep = timestep
                                )
        if restraints is not None:
            self.kernel.set_restraints(restraints)
        self.kernel.set_outputs(energy_out, restart_out, traj_out)

        self.make_job(input_file_name=job_name,
                    output_file_name=job_name,
                    input_structure=input_structure,
                    run_path=path)
        self.current_job.to_gpu()

        if hpc_sub:
            if self.base_slurm is None:
                self.base_slurm = Slurm()
            slurm_sub = copy.deepcopy(self.base_slurm)
            slurm_sub.set_gpus(1)
            slurm_sub.define_dirs(path, os.path.join(slurm_sub.hpc_run_dir, path))
            slurm_sub.set_name(job_name)
            slurm_sub.set_ntasks(self.num_cpu)
            self.current_job.attach_slurm(slurm_sub)

        self.jobs.append(self.current_job)
