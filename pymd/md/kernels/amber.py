"""#TODO
"""

import subprocess
import os
import copy

from pymd.user_configs.amber_defaults import AmberConfig
from pymd.tools import io


class Amber:
    """#TODO

    """
    defaults: AmberConfig
    config: AmberConfig
    parm_file: str
    cores: int

    def __init__(
            self,
            config: AmberConfig = AmberConfig()) -> None:
        self.defaults = copy.deepcopy(x = config)
        self.config = copy.deepcopy(x = config)

    def _gen_runlines(
            self,
            input_file_name: str,
            input_structure_name: str,
            output_file_name: str|None = None,
            gpu: bool = False) -> str:
        """Generates the command that runs the AMBER calculation

        Args:
            input_file_name (str): input file name without the extension.
            input_structure_name (str): Name of coordinate file that the simulation starts from.
            output_file_name (str): Name of output file. Defaults to None, in which case it is 
                the same as input_file_name. Defaults to None.
            gpu (bool): Whether to use the gpu or not. Defaults to False (sander).
        """
        if output_file_name is None:
            output_file_name = input_file_name
        if gpu:
            return f"pmemd.cuda -O -i {input_file_name}.in -p {self.parm_file} -c {input_structure_name} -ref {input_structure_name} " \
                + f"-o {output_file_name}.out -r {output_file_name}.rst7" \
                +f" -x {output_file_name}.nc"
        else:
            return f"sander -O -i {input_file_name}.in -p {self.parm_file} -c {input_structure_name} -ref {input_structure_name} " \
                + f" -o {output_file_name}.out -r {output_file_name}.rst7" \
                + f" -x {output_file_name}.nc"

    def exec(
            self,
            input_file_name: str,
            output_file_name: str,
            input_structure_name: str,
            gpu: bool = False,
            path: str = "./") -> subprocess.CompletedProcess[bytes]:
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
        inputfile = self.config.gen_input_file(filename = input_file_name)
        io.text_dump(inputfile, os.path.join(path, f"{input_file_name}.in"))

        assert os.path.isfile(path = os.path.join(path, input_structure_name)), \
            f"Input structure file is not found: {input_structure_name}"

        command = self._gen_runlines(input_file_name = input_file_name,
                            input_structure_name = input_structure_name,
                            output_file_name = output_file_name,
                            gpu = gpu)

        print(f"INFO: Running command: {command} in {path}")

        output = subprocess.run(args = command.split(), cwd=path, check=True)
        return output

    def set_global(
            self,
            parmfile: str) -> None:
        """
        Defines the parameter and coordinate files for the initial structure. 

        Args:
            param (str): .parm7 file
        """
        self.parm_file = parmfile


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


    def set_cores(
            self,
            cores: int) -> None:
        """Sets the number of cores to use for the MD simulation

        Args:
            cores (int): number of CPU's to run on
        """
        assert cores > 0, "Cannot have a negative number of CPU's"
        self.cores = cores


    def set_restraints(self, restraint_mask: str|None, restraint_wt: float = 5.0) -> None:
        """
        Allows for simple restraints using ambers selection algebra

        Args:
            restraint_mask (str): Atom selection
            restraint_wt (float, optional): Harmonic restraint weight. Defaults to 5.0.
        """
        self.config.set_restraints(restraint_mask=restraint_mask, restraint_wt=restraint_wt)


    def set_ensemble(self, ensemble:str, steps: int,  **kwargs) -> None:
        """
        Initialise an ensemble for the simulation. Allowed ensembles are: min, heat, nvt, npt
        """
        ensemble = ensemble.casefold()
        known_ensembles = ["min", "heat", "nvt", "npt"]
        if ensemble not in known_ensembles:
            raise ValueError(f"Ensemble {ensemble} not recognised," \
                             + f" known ensembles are: {known_ensembles}")
        if ensemble == "min":
            # assert "steps" in kwargs, "Must provide number of steps for minimisation ensemble"
            # steps = kwargs["steps"]
            if "steps_steepest" in kwargs:
                steps_steepest = kwargs["steps_steepest"]
            else:
                steps_steepest = None
            self.config.set_minimisation(steps_total=steps, steps_steepest=steps_steepest)
        elif ensemble == "heat":
            # assert "steps" in kwargs, "Must provide number of steps for heating ensemble"
            # steps = kwargs["steps"]
            self.config.set_ensemble("heat")

            ## Obtain thermostat, if not provided use default
            if "thermostat" in kwargs:
                self.config.set_thermostat(thermostat=kwargs["thermostat"])
            else:
                self.config.set_thermostat(thermostat=self.defaults.ntt)
            ## Usually you are heating from zero. So are not restarting a dynamics simulation.
            if "restart" in kwargs:
                self.config.restart_dynamics(restart=kwargs["restart"])
            else:
                self.config.restart_dynamics(restart=False)

            ## Figure out how many steps to heat for, if not provided use default
            if "heating_steps" in kwargs:
                heating_steps = kwargs["heating_steps"]
            else:
                heating_steps = int(0.9*steps) ## By default, heat for 90% of the simulation, \
                                            # then run at constant temperature for the remaining 10%

            ## Obtain the heating parameters, if not provided use defaults
            if "start_temp" in kwargs:
                start_temp = kwargs["start_temp"]
            else:
                start_temp = self.defaults.tempi
            if "end_temp" in kwargs:
                end_temp = kwargs["end_temp"]
            else:
                end_temp = self.defaults.temp0

            self.config.set_heating(start_temp=start_temp, end_temp=end_temp, nsteps=heating_steps)

            if "timestep" in kwargs:
                dt = kwargs["timestep"]
            elif "time_step" in kwargs:
                dt = kwargs["time_step"]
            else:
                dt = self.defaults.dt

            if "shake" in kwargs:
                shake = kwargs["shake"]
            else:
                shake = self.defaults.ntc

            self.config.set_dynamics(timestep=dt, shake=shake)
            self.config.nstlim = steps
        elif ensemble == "nvt":
            # assert "steps" in kwargs, "Must provide number of steps for heating ensemble"
            # steps = kwargs["steps"]

            ## Obtain thermostat, if not provided use default
            if "thermostat" in kwargs:
                self.config.set_thermostat(thermostat=kwargs["thermostat"])
            else:
                self.config.set_thermostat(thermostat=self.defaults.ntt)
            ## Usually you are restarting a dynamics simulation.
            if "restart" in kwargs:
                self.config.restart_dynamics(restart=kwargs["restart"])
            else:
                self.config.restart_dynamics(restart=True)

            ## Obtain the heating parameters, if not provided use defaults
            if "temperature" in kwargs:
                temp = kwargs["temperature"]
            else:
                temp = self.defaults.temp0


            self.config.set_temperature(temperature=temp)
            self.config.set_pressure_scaling(pressure_scaling=0) # No pressure scaling for NVT ensemble

            if "timestep" in kwargs:
                dt = kwargs["timestep"]
            elif "time_step" in kwargs:
                dt = kwargs["time_step"]
            else:
                dt = self.defaults.dt

            if "shake" in kwargs:
                shake = kwargs["shake"]
            else:
                shake = self.defaults.ntc

            self.config.set_dynamics(timestep=dt, shake=shake)
            self.config.set_ensemble(ensemble="nvt")
            self.config.nstlim = steps
        elif ensemble == "npt":
            # assert "steps" in kwargs, "Must provide number of steps for npt ensemble"
            # steps = kwargs["steps"]

            ## Obtain thermostat, if not provided use default
            if "thermostat" in kwargs:
                self.config.set_thermostat(thermostat=kwargs["thermostat"])
            else:
                self.config.set_thermostat(thermostat=self.defaults.ntt)
            ## Usually you are restarting a dynamics simulation.
            if "restart" in kwargs:
                self.config.restart_dynamics(restart=kwargs["restart"])
            else:
                self.config.restart_dynamics(restart=True)

            ## Obtain the heating parameters, if not provided use defaults
            if "temperature" in kwargs:
                temp = kwargs["temperature"]
            else:
                temp = self.defaults.temp0

            if "pressure_scaling" in kwargs:
                self.config.set_pressure_scaling(pressure_scaling=kwargs["pressure_scaling"])
            else:
                self.config.set_pressure_scaling(pressure_scaling=self.defaults.ntp)

            if "barostat" in kwargs:
                self.config.set_barostat(barostat=kwargs["barostat"])
            else:
                self.config.set_barostat(barostat=self.defaults.ntb)

            self.config.set_temperature(temperature=temp)

            if "timestep" in kwargs:
                dt = kwargs["timestep"]
            elif "time_step" in kwargs:
                dt = kwargs["time_step"]
            else:
                dt = self.defaults.dt

            if "shake" in kwargs:
                shake = kwargs["shake"]
            else:
                shake = self.defaults.ntc

            if "pressure" in kwargs:
                pressure = kwargs["pressure"]
                self.config.set_pressure(pressure=pressure)
            else:
                self.config.set_pressure(pressure=self.defaults.pres0)

            self.config.set_dynamics(timestep=dt, shake=shake)
            self.config.set_ensemble(ensemble="npt")
            self.config.nstlim = steps


    def _reset_config(self) -> None:
        """Reset the configuration to defaults."""
        self.config = copy.deepcopy(x=self.defaults)
