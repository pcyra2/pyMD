"""#TODO
"""
import copy

from pymd.md.md import MDClass, MDJobClass
from pymd.tools.slurm import Slurm
from pymd.user_configs.amber_defaults import AmberConfig
from pymd.tools import convert



class Amber(MDClass):
    """#TODO

    """
    defaults: AmberConfig
    config: AmberConfig

    _sc_mask_1: str|None = None
    _sc_mask_2: str|None = None
    _ti_mask_1: str|None = None
    _ti_mask_2: str|None = None


    def __init__(self,
            start_coordinates: str,
            parm_file: str,
            config: AmberConfig = AmberConfig()) -> None:
        super().__init__(start_coordinates = start_coordinates, parm_file = parm_file)
        self.defaults = copy.deepcopy(x = config)
        self.config = copy.deepcopy(x = config)
        self.defaults._param_file = parm_file
        self.config._param_file = parm_file


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


    def set_restraints(self, restraint: str = "all_not_solvent", restraint_wt: float = 5.0) -> None:
        """
        Allows for simple restraints using ambers selection algebra

        Args:
            restraint (str): 
            restraint_wt (float, optional): Harmonic restraint weight. Defaults to 5.0.
        """
        restraint_mask: str
        if restraint == "all_not_solvent":
            restraint_mask  = "'!(WAT NA+ CL-)'"
        elif restraint == "protein":
            restraint_mask = f"':{self.protein_start}-{self.protein_end}'"
        elif restraint == "ligand":
            if isinstance(self.ligands, int):
                self.ligands = [self.ligands]
            restraint_mask = ":"
            for lig in self.ligands:
                restraint_mask += f"{lig},"
        elif restraint == "backbone":
            restraint_mask = "'@CA,N,C'"
        else:
            raise ValueError(f"Unrecognised restraint {restraint}")
        # print(f"INFO: Applying restraints with mask {restraint_mask} and weight {restraint_wt}")
        self.config.set_restraints(restraint_mask=restraint_mask,
                                   restraint_wt=restraint_wt)


    def set_minimisation(self,
            steps: int,
            steps_steepest: int|None = None
            ) -> None:
        """Initialises standard minimisation parameters

        Args:
            steps (int): Total number of minimisation steps
            steps_steepest (int, optional): Number of steepest-descent gradient steps to perform
        """
        self.config.set_minimisation_variables(steps_total=steps,
                                                steps_steepest=steps_steepest)
        self.config.clear_attribute(attribute="nstlim")
        self.config.set_ensemble(ensemble="min")


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
        self.config.set_dynamics(steps = total_steps,
                                 timestep=convert.time(in_time=time_step,
                                                    in_unit="fs",
                                                    out_unit="ps"))
        if heating_steps is None:
            heating_steps = total_steps
        self.config.set_heating(start_temp=start_temperature,
                                end_temp=end_temperature,
                                nsteps=heating_steps)
        if thermostat is not None:
            self.defaults.set_thermostat(thermostat = thermostat)
        self.config.set_thermostat(thermostat = self.defaults.ntt)
        self.config.restart_dynamics(restart=continue_dynamics)
        self.config.set_ensemble(ensemble = "heat")


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
        self.config.set_dynamics(steps = steps, timestep=convert.time(in_time=time_step,
                                                                    in_unit="fs",
                                                                    out_unit="ps"))
        self.config.set_temperature(temperature=temperature)
        self.config.restart_dynamics(True)
        if thermostat is not None:
            self.defaults.set_thermostat(thermostat = thermostat)
        self.config.set_thermostat(thermostat = self.defaults.ntt)
        self.config.set_pressure_scaling(pressure_scaling = 0)
        for attr in ["barostat", "pres0"]:
            self.config.clear_attribute(attr)
        
        self.config.restart_dynamics(restart=continue_dynamics)
        self.config.set_ensemble(ensemble="nvt")


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
        self.config.set_dynamics(steps = steps, timestep=convert.time(in_time=time_step,
                                                                    in_unit="fs",
                                                                    out_unit="ps"))
        self.config.set_temperature(temperature=temperature)
        self.config.restart_dynamics(True)
        if thermostat is not None:
            self.defaults.set_thermostat(thermostat = thermostat)
        self.config.set_thermostat(thermostat = self.defaults.ntt)
        
        if pressure_scaling is not None:
            self.config.set_pressure_scaling(pressure_scaling = pressure_scaling)
        else:
            self.config.set_pressure_scaling(pressure_scaling = self.defaults.ntp)
        
        if barostat is not None:
            self.defaults.set_barostat(barostat = barostat)
        self.config.set_barostat(barostat = self.defaults.barostat)

        if pressure is not None:
            self.config.set_pressure(pressure=pressure)
        
        self.config.restart_dynamics(restart=continue_dynamics)
        self.config.set_ensemble(ensemble = "npt")


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
        """Builds the config and converts into a Job with a kernel. 
        
        Args:
            input_file_name (str): The name of the input file.
            input_structure (str): The name of the input coordinate file. 
            output_file_name (str): The name of the output file. 
            run_path (str): The path to run the calculation. 
            gpu (bool): Whether to run the calculation on a GPU. 
            hpc (Slurm|None): Whether to assign a HPC object to the calculation. 
        """
        if self._sc_mask_1 != None:
            self.config.ntf = 1
        self.latest_job = MDJobClass(inputfile_name=input_file_name,
                input_structure=input_structure,
                outputfile_name=output_file_name,
                run_path=run_path)
        self.latest_job.add_kernel(config = self.config)
        if gpu:
            self.latest_job.to_gpu()
        if hpc is not None:
            self.add_HPC(hpc=hpc)
        self.jobs.append(self.latest_job)
        self._reset_config()


    def init_ti(self,
            scmask_1: str,
            timask_1: str,
            scmask_2: str,
            timask_2: str) -> None:
        self._sc_mask_1 = scmask_1
        self._sc_mask_2 = scmask_2
        self._ti_mask_1 = timask_1
        self._ti_mask_2 = timask_2

    def set_ti(self,
            lam:float,
            mbar: bool = False,
            lambda_list: list[float] = []) -> None:
        self.config.initialise_ti(ti_mask_1=self._ti_mask_1,
                        ti_mask_2 = self._ti_mask_2,
                        sc_mask_1 = self._sc_mask_1,
                        sc_mask_2 = self._sc_mask_2,
                        mbar=mbar,
                        lambda_list=lambda_list)
        self.config.set_lambda_value(lambda_value=lam)