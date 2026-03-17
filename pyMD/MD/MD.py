from pyMD.MD.kernels.universal import MDJobClass
from pyMD.MD.kernels.AMBER import Amber
from pyMD.UserConfigs.AmberDefaults import AmberConfig
import pyMD.tools.convert as convert

class MDClass:
    base_config: AmberConfig
    _backend: str
    kernel: Amber
    jobs: list[MDJobClass]
    current_job: MDJobClass   
    num_CPU: int = 1
    num_GPU: int = 0


    def __init__(self, backend: str = "", config: AmberConfig = AmberConfig()):
        self._backend = backend.casefold()
        self.base_config = config

        if self._backend == "amber":
            self.kernel = Amber(config)
        else:
            raise NotImplementedError(f"ERROR: Backend {self._backend} not implemented yet, only AMBER is currently supported")
        self.jobs = []


    def set_parmfile(self, parmfile:str):
        self.kernel.set_global(parmfile)


    def define_Hardware(self, CPU: int=1, GPU:int = 0 ):
        self.num_CPU=CPU
        self.num_GPU=GPU


    def make_job(self, input_file_name: str, input_structure: str, output_file_name: str, run_path: str ):
        self.kernel.config.set_calculation_variables(self.kernel.parmfile,
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


    def minimize(self, input_structure: str, job_name: str, steps: int, restraints: str|None = None, run_path: str = "./", steps_steepest: int|None = None, traj_out: int = 10, restart_out: int = 10, energy_out: int = 10):
        """Sets up a minimisation job with the given parameters and adds it to the list of jobs to be executed.

        Args:
            input_structure (str): Name of the input structure file (e.g. .rst7 for AMBER).
            job_name (str): Name of the job, used for naming input and output files.
            steps (int): Number of steps to run the minimisation for.
            restraints (str, optional): Selection algebra for restraints. Defaults to "".
            run_path (str, optional): Path where the job will be executed. Defaults to "./".
            steps_steepest (int, optional): Number of steepest descent minimization steps. Defaults to 0.
            traj_out (int, optional): Frequency of trajectory output. Defaults to 10.
            restart_out (int, optional): Frequency of restart output. Defaults to 10.
            energy_out (int, optional): Frequency of energy output. Defaults to 10.
        """
        self.kernel.set_ensemble(ensemble="min", steps=steps, steps_steepest=steps_steepest)
        self.kernel.set_restraints(restraints, self.kernel.config.restraint_wt)

        self.kernel.set_outputs(energy_out, restart_out, traj_out)

        self.make_job(input_file_name=job_name,
                    input_structure=input_structure,
                    output_file_name=job_name,
                    run_path=run_path,
                    )
        self.jobs.append(self.current_job)


    def heat(self, 
            input_structure: str, 
            job_name: str, 
            steps: int, 
            start_temperature: float = 0, 
            end_temperature: float = 300, 
            restraints: str|None = None, 
            timestep: float = convert.time(2, in_unit="fs", out_unit="ps"), 
            thermostat: str|None = None,
            traj_out: int = 100,
            energy_out: int = 10,
            restart_out: int = 10,
            path: str = "./"):
        """Performs a standard heating workflow on the system

        Args:
            input_structure (str): Coordinates to heat
            job_name (str): Name of job
            steps (int): Number of steps
            start_temperature (float, optional): Initial temperature. Defaults to 0.
            end_temperature (float, optional): End temperature. Defaults to 300.
            restraints (str | None, optional): Any restraints to apply to the system. Defaults to None.
            timestep (float, optional): timestep for dynamics in picoseconds. Defaults to 0.002 ps (2 fs).
            thermostat (str | None, optional): Desired thermostat. Defaults to the kernel's default thermostat.
            traj_out (int, optional): frequency to update trajectory. Defaults to 100.
            energy_out (int, optional): Frequency to print energy. Defaults to 10.
            restart_out (int, optional): Frequency to update restart structure. Defaults to 10.
            path (str, optional): _description_. Defaults to "./".
        """
        if thermostat == None:
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
        self.jobs.append(self.current_job)

