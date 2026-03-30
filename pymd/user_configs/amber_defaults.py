"""#TODO
"""
import os
import pymd.tools.convert as convert


class AmberConfig:
    """Contains information an AMBER input job. It allows for settings up 
    default variables.

    Attributes:
        # User defined variables:

        ## Software paths
        _GPUPath (str): Path to the GPU executable
        _CPUPath (str): Path to the CPU executable

        ## IO options

        ntpr (int): Frequency to write mdout energy
        ntwx (int): Frequency to write to mdcrd trajectory file
        ntwr (int): Frequency to update the restart file
        ioutfm (int): Writes netCDF trajectories as binary
        iwrap (int): Wraps the trajectories into the "primary box"

        ## Minimisation options
        maxcyc (int): Maximum number of minimisation steps
        imin (int): Whether to run minimization or dynamics simulation
        ncyc (int): When to swap from steepest-descent to conjugate gradient minimisation
        ntmin (int): Type of minimisation to perform

        ## Simulation options

        irest (int): Whether to restart the simulation, 0 = new simulation, 1 = continue simulation
        cut (float): Non-bonded cutoff distance (Angstrom)
        ntx (int): Whether to read coordinates and velocities from the restart file, 1 = no, 5 = yes

        ## Dynamics options
        dt (float): Dynamics time step in picoseconds
        nstlim (int): Number of Molecular dynamics steps to perform
        ig (int): Initial seed. -1 is random


        ## Retraints and potentials
        nct (int): Shake setting, 1 = No shake, 2 = X-H bonds, 3 = all bonds
        ntf (int): Force evolution, 1=all forces, 2=all except H (NTC=2), 3=None (NTC=3)
        jfastw (int): Fast water setting for shake, set to 4 if not desired
        dielec (float): Dielectric constant for electrostatic interactions.
        ntr (int): Toggles restraint_mask and restraint_wt
        restraintmask (str): Restrain all atoms except for solvent & counter atoms
        restraint_wt (float):  Restrain with 5 kcal#mol potential
        nmropt (int): NMR weights to be read

        ## Ensemble Settings
        ntb (int): PBC control. 0=No periodicity, 1=constant volume, 2=constant pressure

        ## Temperature Settings
        ntt (int): Temperature scaling, 2=anderson, 3=Langevin, 9=Nose-Hoover, 11=Berendsen
        temp0 (float): Final temperature of the simulation
        tempi (float): Initial temperature of the simulation
        gamma_ln (float): Collision frequency

        ## Pressure Settings
        ntp (int): Pressure scaling, 1=isotropic (Recommended), 2=anisotropic, 3=semiisotropic, 
            4=targeted volume
        barostat (int): Barostat, 1=Berendsen, 2=MonteCarlo
        pres0 (float): Reference pressure (bar)

        # Internal variables.

        _minimisation (bool): Whether the calculation is minimisation or not.
        _initialised (bool): Whether the calculation is initialised
        _heating_steps (int): Number of heating steps for the simulation
        _input_file_name (str): Name of the inputfile
        _output_file_name (str): Name of the output file
        _param_file (str): Name of the parameter file
        _input_coord_file (str): Name of the input coordinates.

        ## Thermodynamic Integration config
        icfe (int): Whether to do a free energy calculation. 0 = No, 1 = Yes
        clambda (float): Value of Lambda
        timask1 (str): Selects the atoms unique in system 1
        timask2 (str): Selects the atoms unique in system 2

        ## Soft Core config
        ifsc (int): Whether to use soft core potentials. 0 = No, 1 = Yes
        scalpha (float): Alpha parameter. Defaults to 0.5
        scbeta (float): The Beta parameter for SoftCore. Defaults to 12
        logdvdl (int): dumps dv/dlam at the end for processing
        scmask1 (str): The mask for soft core atoms in system 1
        scmask2 (str): The mask for soft core atoms in system 2

        ## MBAR config
        ifmbar (int): Whether to generate MBAR outputs. 0 = No, 1 = Yes
        mbar_states (int): The  total number of Lambda windows
        mbar_lambda (str): A list of comma sepparated floats defining the lambda windows
            e.g. `0.0, 0.2, 0.4, 0.6, 0.8, 1.0,`
    """
    _GPUPath: str = "" # Path to the GPU binary of AMBER
    _CPUPath: str = "" # Path to the CPU binary of AMBER

    ## IO options
    ntpr: int = 100 # Frequency to write mdout energy
    ntwx: int = 100 # Frequency to write to mdcrd trajectory file
    ntwr: int = 100 # Frequency to update the restart file
    ioutfm: int = 1 # Writes netCDF trajectories as binary
    iwrap: int = 1 # Wraps the trajectories into the "primary box"

    ## Minimisation options
    maxcyc: int = 300 # Maximum number of minimisation steps
    imin: int = 0 # Whether to run minimization or dynamics simulation
    ncyc: int = 100 # When to swap from steepest-descent to conjugate gradient minimisation
    ntmin: int = 1 # Type of minimisation to perform

    ## Simulation options

    irest: int = 0 # Whether to restart the simulation, 0 = new simulation, 1 = continue simulation
    cut: float = 8 # Non-bonded cutoff distance (Angstrom)
    ntx: int = 1 # Whether to read coordinates and velocities from the restart file, 1 = no, 5 = yes

    ## Dynamics options
    dt: float = 0.002 # Dynamics time step in picoseconds
    nstlim: int = 1000 # Number of Molecular dynamics steps to perform
    ig: int = -1 # Initial seed. -1 is random


    ## Retraints and potentials
    nct: int = 2 # Shake setting, 1 = No shake, 2 = X-H bonds, 3 = all bonds
    ntf: int = 1 # Force evolution, 1=all forces, 2=all except H (NTC=2), 3=None (NTC=3)
    jfastw: int = 0 # Fast water setting for shake, set to 4 if not desired
    dielec: float = 1.0 # Dielectric constant for electrostatic interactions.
    ntr: int = 0 # Toggles restraint_mask and restraint_wt
    restraintmask: str = "'!(:WAT,NA,CL)'" # Restrain all atoms except for solvent & counter atoms
    restraint_wt: float = 5.0 # Restrain with 5 kcal#mol potential
    nmropt: int = 1 # NMR weights to be read

    ## Ensemble Settings
    ntb: int = 0 # PBC control. 0=No periodicity, 1=constant volume, 2=constant pressure

    ## Temperature Settings
    ntt: int = 3 # Temperature scaling, 2=anderson, 3=Langevin, 9=Nose-Hoover, 11=Berendsen
    temp0: float = 300.0 # Final temperature of the simulation
    tempi: float = 0.0 # Initial temperature of the simulation
    gamma_ln: float = 2.0 # Collision frequency

    ## Pressure Settings
    ntp: int = 0 # Pressure scaling, 1=isotropic (Recommended),
        # 2=anisotropic, 3=semiisotropic, 4=targeted volume
    barostat: int = 1 # Barostat, 1=Berendsen, 2=MonteCarlo
    pres0: float = 1.0 # Reference pressure (bar)

    ##### Do not edit beyond this point #####
    _minimisation: bool = False
    _initialised: bool = False
    _heating_steps: int = 1
    _input_file_name: str
    _output_file_name: str
    _param_file: str
    _input_coord_file: str

    ## Thermodynamic Integration config
    icfe: int = 0 # whether to do a free energy calculation. 0 = No, 1 = Yes
    clambda: float # Value of Lambda
    timask1: str # Selects the atoms unique in system 1
    timask2: str # Selects the atoms unique in system 2

    ## Soft Core config
    ifsc: int = 0 # Whether to use soft core potentials. 0 = No, 1 = Yes
    scalpha: float = 0.5 # Alpha parameter. Defaults to 0.5
    scbeta: float = 12 # The Beta parameter for SoftCore. Defaults to 12
    logdvdl: int = 0 # dumps dv/dlam at the end for processing
    scmask1: str # The mask for soft core atoms in system 1
    scmask2: str # The mask for soft core atoms in system 2

    ## MBAR config
    ifmbar: int = 0 # Whether to generate MBAR outputs. 0 = No, 1 = Yes
    mbar_states: int # The  total number of Lambda windows
    mbar_lambda: str # A list of comma sepparated floats defining the lambda windows
        # e.g. `0.0, 0.2, 0.4, 0.6, 0.8, 1.0,`

    def __init__(self) -> None:
        if os.path.isfile(path=self._CPUPath) is False:
            print("WARNING: AMBER CPU path not found, please fix this to use amber CPU")
            print(self._CPUPath)
        if os.path.isfile(path=self._GPUPath) is False:
            print("WARNING: AMBER GPU path not found, please fix this to use amber CPU")
            print(self._GPUPath)

    def set_timestep(self, timestep: float) -> None:
        """

        This method sets the time step for the simulation.

        Args:
            timestep (float): The new time step in nanoseconds. It should be a positive number.

        Notes:
            The time step is used to determine how often the positions and velocities 
            of the particles are updated. A smaller time step can lead to more accurate results, 
            but also increases the computational cost.

        Examples:
            >>> config.set_timestep(0.001)
            This sets the time step to 1 picosecond (ps).
        """
        assert timestep > 0, f"ERROR: Cannot have a negative timestep: {timestep} not allowed"
        self.dt = timestep

    def set_minimisation(self, steps_total: int, steps_steepest: int|None = None) -> None:
        """Changes the configuration to run a minimisation rather than a dynamics simulation

        Args:
            steps_total (int): Total number of minimisation steps
            steps_steepest (int | None, optional): Number of steepest descent steps to take before 
            swapping to conjugate gradient. If None, it will be changed to steps_total/2. Defaults 
            to None.
        """
        assert steps_total >= 0, "ERROR: Cannot run for negative "\
            + f"steps, ({steps_total} not allowed)"
        if steps_steepest is None:
            steps_steepest = int(steps_total/2)
        self.imin = 1
        self._minimisation = True
        self.ncyc = steps_steepest
        self.maxcyc = steps_total

    def set_dynamics(self, timestep:float = 0.002, shake: int = 1, timestep_units: str = "ps") -> None:
        """Changes the configuration to run a dynamics simulation
        
        Args:
            timestep (float, optional): Timestep to use for dynamics simulation. Defaults to 2 ps.
            shake (int, optional): The nct configuration to use. 1 = no shake, 2 is restrain 
            X-H bonds, 3 is shake all bonds. Defaults to 1.
        """
        self.imin = 0
        self._minimisation = False
        self._update_timestep(timestep=timestep, timestep_units=timestep_units)
        self.nct = shake
        if self._check_timestep_compatibility() is False:
            self.nct = 2

    def _check_timestep_compatibility(self) -> bool:
        """Checks that the timestep and the shake are compatible with each other

        Returns:
            bool: True/False depending on compatibility
        """
        if self.nct == 1 and self.dt < 0.001:
            return True
        elif self.nct > 1:
            return True
        else:
            return False

    def _update_timestep(self, timestep: float = 0.002, timestep_units: str = "ps") -> None:
        
        self.dt = convert.time(in_time=timestep, in_unit=timestep_units, out_unit="ps")

    def to_dict(self)->dict:
        """Returns a dictionary of the class attributes"""
        return {key:value for key, value in vars(self).items() if not key.startswith('_')}
    
    def set_outputs(self, energy: int, restart: int, trajectory: int) -> None:
        """Sets the output frequencies for the calculation. 

        Args:
            energy (int): how frequently to print the energy (and other associated values)
            restart (int): how frequently to update the restart coordinates
            trajectory (int): how frequently to write to the trajectory file
        """
        self.ntpr = energy
        self.ntwr = restart
        self.ntwx = trajectory

    def set_restraints(self, restraint_mask: str|None, restraint_wt: float) -> None:
        """
        Allows for simple restraints using ambers selection algebra

        Args:
            restraint_mask (str|None): Atom selection
            restraint_wt (float, optional): Harmonic restraint weight. Defaults to 5.0.
        """
        if restraint_mask is not None:
            self.ntr = 1
            self.restraintmask = restraint_mask
            self.restraint_wt = restraint_wt
        else:
            self.ntr = 0
            try:
                del self.restraintmask
            except NameError:
                # del self.restraintmask
                pass


            try:
                del self.restraint_wt
            except NameError:
                # del self.restraint_wt
                pass

    def set_temperature(self, temperature: float) -> None:
        """Sets the temperature for the simulation

        Args:
            temperature (float): Temperature in Kelvin
        """
        assert temperature >= 0, f"ERROR: Cannot have a negative temperature, {temperature} not " \
            + "allowed"
        self.set_heating(start_temp=temperature, end_temp=temperature, nsteps=1)

    def set_heating(self, start_temp: float = 0.0, end_temp: float = 300.0, nsteps: int = 1) -> None:
        """Sets the configuration to run a heating simulation
        
        Args:
            start_temp (float, optional): Starting temperature of the simulation. Defaults to 0.0 K.
            end_temp (float, optional): Final temperature of the simulation. Defaults to 300.0 K.
            nsteps (int, optional): Number of steps to heat for. Defaults to 1.
        """
        if "ntt" not in self.to_dict().keys():
            self.set_thermostat(thermostat=self.ntt)
        self.temp0 = end_temp
        self.tempi = start_temp
        self._heating_steps = nsteps
        
    def restart_dynamics(self, restart: bool|int = True) -> None:
        """Sets whether to restart the dynamics simulation or not

        Args:
            restart (bool, optional): Whether to restart the simulation or not. 
            Defaults to True. (Can also supply irest as 0/1 for backwards compatibility)
        """
        if isinstance(restart, int):
            if restart == 0:
                restart = False
            elif restart == 1:
                restart = True
            else:
                raise ValueError(f"ERROR: Restart must be a boolean or 0/1, {restart} not allowed")

        if restart:
            self.irest = 1
            self.ntx = 5
        else:
            self.irest = 0
            self.ntx = 1

    def set_thermostat(self, thermostat: int|str) -> None:
        """Sets the thermostat for the simulation.

        Args:
            thermostat (int | str): Thermostat to use for the simulation. Can be supplied as a 
            string or an int. Allowed thermostats are: "none"/0, "anderson"/2, "langevin"/3, 
            "nose_hoover"/9, "berendsen"/11

        """
        if isinstance(thermostat, str):
            thermostat_int = THERMOSTATS.get(thermostat.casefold())
            if thermostat_int is None:
                raise ValueError(f"Thermostat {thermostat} not recognised, known " \
                                + f"thermostats are: {list(THERMOSTATS.keys())}")
        elif isinstance(thermostat, int):
            if thermostat not in THERMOSTATS.values():
                raise ValueError(f"Thermostat {thermostat} not recognised, known " \
                                + f"thermostats are: {list(THERMOSTATS.values())}")
            thermostat_int = thermostat
        self.ntt = thermostat_int

    def set_pressure_scaling(self, pressure_scaling: int|str) -> None:
        """Sets the pressure scaling for the simulation

        Args:
            pressure_scaling (int | str): Pressure scaling algoithm to use. Can be supplied as a 
            string or an int. Allowed values are: "none"/0, "isotropic"/1, "anisotropic"/2, 
            "semiisotropic"/3, "target_volume"/41
        """
        if isinstance(pressure_scaling, str):
            pressure_scaling_int = PRESSURE_SCALING.get(pressure_scaling.casefold())
            if pressure_scaling_int is None:
                raise ValueError(f"Pressure scaling {pressure_scaling} not recognised, " \
                                + f"known pressure scalings are: {list(PRESSURE_SCALING.keys())}")
        elif isinstance(pressure_scaling, int):
            if pressure_scaling not in PRESSURE_SCALING.values():
                raise ValueError(f"Pressure scaling {pressure_scaling} not recognised, " \
                                + f"known pressure scalings are: {list(PRESSURE_SCALING.values())}")
            pressure_scaling_int = pressure_scaling
        assert isinstance(pressure_scaling_int, int), "Pressure scaling should be an int."
        self.ntp = pressure_scaling_int

    def set_ensemble(self, ensemble: str) -> None:
        """
        Initialise an ensemble for the simulation. Allowed ensembles are: min, heat, nvt, npt

        Args:
            ensemble (str): The ensemble to use for the simulation. 
                Allowed ensembles are: min, heat, nvt, npt
        """
        ensemble = ensemble.casefold()
        known_ensembles = ["min", "heat", "nvt", "npt"]
        ensemble_int = self.ntb
        if ensemble not in known_ensembles:
            raise ValueError(f"Ensemble {ensemble} not recognised, " \
                            + f"known ensembles are: {known_ensembles}")
        if ensemble == "min":
            ensemble_int = 0
        elif ensemble == "heat":
            ensemble_int = 1
        elif ensemble == "nvt":
            ensemble_int = 1
        elif ensemble == "npt":
            ensemble_int = 2
        self.ntb = ensemble_int

    def set_barostat(self, barostat: int|str) -> None:
        """Sets the barostat for the simulation

        Args:
            barostat (int | str): Barostat to use for the simulation. Can be supplied as a 
            string or an int. Allowed values are: "berendsen"/1, "monte_carlo"/2
        """
        barostat_int = self.barostat
        if isinstance(barostat, str):
            barostat_int = BAROSTATS.get(barostat.casefold())
            if barostat_int is None:
                raise ValueError(f"Barostat {barostat} not recognised, known barostats are: {list(BAROSTATS.keys())}")
        elif isinstance(barostat, int):
            barostat_int = barostat
            if barostat_int not in BAROSTATS.values():
                raise ValueError(f"Barostat {barostat} not recognised, known barostats are: {list(BAROSTATS.values())}")
        else:
            raise ValueError(f"Barostat {barostat} not recognised.")
        self.barostat = barostat_int

    def set_pressure(self, pressure: float) -> None:
        """Sets the pressure for the simulation

        Args:
            pressure (float): Pressure in bar
        """
        assert pressure >= 0, f"ERROR: Cannot have a negative pressure, {pressure} not allowed"
        if "barostat" not in self.to_dict().keys():
            self.set_barostat(barostat=self.barostat)
        if "ntp" not in self.to_dict().keys():
            self.set_pressure_scaling(pressure_scaling=self.ntp)
        self.pres0 = pressure

    def gen_input_file(self, filename: str) -> list[str]:
        """Generates an AMBER input file from the current configuration

        Args:
            filename (str): The name of the input file to generate
        
        Returns:
            list[str]: The lines of the input file to write
        """

        header = f"{filename} Generated by pyMD, CopyRight (C) 2026 Ross Amory\n&cntrl"
        config = self.to_dict()
        body = [f"{key} = {value}" for key, value in config.items()]
        footer = "/"

        if "tempi" in config and "temp0" in config: # Add the heating section if we are heating
            if config["tempi"] != config["temp0"]:
                footer += f"""
&wt type'TEMP0' istep1=0, istep2={self._heating_steps}, value1={self.tempi}, value2={self.temp0} /
&wt type 'TEMP0', istep1={int(self._heating_steps)+1}, istep2={self.maxcyc}, value1={self.temp0}, value2={self.temp0} /
&wt  type='END' /
"""
        return [header] + body + [footer]

    def set_calculation_variables(self, paramfile: str, input_coordinates: str, input_file_name: str, output_file_name: str) -> None:
        """Sets some basic calculation information

        Args:
            paramfile (str): The parameter file to use for the simulation, usually a .parm7 file
            input_coordinates (str): The coordinate file to use for the simulation, 
                usually a .rst7 file
            input_file_name (str): The name of the input file to generate
            output_file_name (str): The name of the output file to generate
        """
        self._param_file = paramfile
        self._input_coord_file = input_coordinates
        self._input_file_name = input_file_name
        self._output_file_name = output_file_name

    def initialise_ti(self,
            ti_mask_1: str,
            ti_mask_2: str,
            sc_mask_1: str,
            sc_mask_2: str,
            lambda_list: list[float],
            mbar: bool
            ) -> None:
        """
        #TODO

        Args:
            ti_mask_1 (str): _description_
            ti_mask_2 (str): _description_
            sc_mask_1 (str): _description_
            sc_mask_2 (str): _description_
            lambda_list (list[float]): _description_
            mbar (bool): _description_
        """
        self.icfe=1
        self.timask1 = ti_mask_1
        self.timask2 = ti_mask_2

        self.ifsc = 1
        self.scmask1 = sc_mask_1
        self.scmask2 = sc_mask_2
        self.scalpha = self.scalpha
        self.scbeta = self.scbeta
        self.logdvdl = self.logdvdl

        if mbar:
            self.ifmbar = 1
            self.mbar_states = len(lambda_list)
            lambda_str = str(lambda_list[0])
            for lam in lambda_list[1:]:
                lambda_str += f",{lam}"
            self.mbar_lambda = lambda_str


    def set_lambda_value(self, lambda_value: float) -> None:
        """
        #TODO

        Args:
            lambda_value (float): _description_
        """
        self.clambda = lambda_value

THERMOSTATS = dict(none = 0,
                   anderson = 2,
                   langevin = 3,
                   nose_hoover = 9,
                   berendsen = 11)

PRESSURE_SCALING = dict(none = 0,
                        isotropic = 1,
                        anisotropic = 2,
                        semiisotropic = 3,
                        target_volume = 4)

BAROSTATS = dict(berendsen = 1,
                monte_carlo = 2)
