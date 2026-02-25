import os

class AmberConfig:
    GPUPath:str = "" # Path to the GPU binary of AMBER
    CPUPath:str = "" # Path to the CPU binary of AMBER

    ## IO options
    ntpr:int = 100 # Frequency to write mdout energy
    ntwx:int = 100 # Frequency to write to mdcrd trajectory file
    ntwr:int = 100 # Frequency to update the restart file
    ioutfm:int = 1 # Writes netCDF trajectories as binary 
    iwrap:int = 1 # Wraps the trajectories into the "primary box"

    ## Minimisation options
    maxcyc:int = 300 # Maximum number of minimisation steps
    imin:int = 0 # Whether to run minimization or dynamics simulation
    ncyc:int = 100 # When to swap from steepest-descent to conjugate gradient minimisation
    ntmin:int = 1 # Type of minimisation to perform

    ## Simulation options
    
    irest:int = 0 # Whether to restart the simulation, 0 = new simulation, 1 = continue simulation
    cut:float = 8 # Non-bonded cutoff distance (Angstrom)

    ## Dynamics options
    dt:float = 0.002 # Dynamics time step
    nstlim:int = 1000 # Number of Molecular dynamics steps to perform
    ig: int = -1 # Initial seed. -1 is random


    ## Retraints and potentials
    nct:int = 2 # Shake setting, 1 = No shake, 2 = X-H bonds, 3 = all bonds
    ntf:int = 1 # Force evolution, 1=all forces, 2=all except H (NTC=2), 3=None (NTC=3)
    jfastw:int = 0 # Fast water setting for shake, set to 4 if not desired
    dielec:float = 1.0 # Dielectric constant for electrostatic interactions.
    ntr:int = 0 # Toggles restraint_mask and restraint_wt
    restraintmask:str = "'!(:WAT,NA,CL)'" # Restrain all atoms except for solvent & counter atoms
    restraint_wt:float = 5.0 # Restrain with 5 kcal#mol potential
    nmropt:int = 1 # NMR weights to be read

    ## Ensemble Settings
    ntb:int = 0 # PBC control. 0=No periodicity, 1=constant volume, 2=constant pressure

    ## Temperature Settings
    ntt:int = 3 # Temperature scaling, 2=anderson, 3=Langevin, 9=Nose-Hoover, 11=Berendsen
    temp0:float = 0.0 # Reference#Final temperature of the simulation
    tempi:float = 0.0 # Initial temperature of the simulation
    gamma_ln:float = 2.0 # Collision frequency

    ## Pressure Settings
    ntp:int = 0 # Pressure scaling, 1=isotropic (Recommended), 2=anisotropic, 3=semiisotropic, 4=targeted volume
    barostat:int = 1 # Barostat, 1=Berendsen, 2=MonteCarlo
    pres0:float = 1.0 # Reference pressure (bar)

    ##### Do not edit beyond this point #####
    _minimisation:bool = False

    def __init__(self):
        if os.path.isfile(self.CPUPath) is False:
            print("WARNING: AMBER CPU path not found, please fix this to use amber CPU")
            print(self.CPUPath)
        if os.path.isfile(self.GPUPath) is False:
            print("WARNING: AMBER GPU path not found, please fix this to use amber CPU")
            print(self.GPUPath)
        
    def set_timestep(self, timestep:float):
        """

        This method sets the time step for the simulation.

        Args:
            timestep (float): The new time step in nanoseconds. It should be a positive number.

        Notes:
            The time step is used to determine how often the positions and velocities of the particles are updated.
            A smaller time step can lead to more accurate results, but also increases the computational cost.

        Examples:
            >>> config.set_timestep(0.001)
            This sets the time step to 1 picosecond (ps).
        """
        assert timestep > 0, f"ERROR: Cannot have a negative timestep: {timestep} not allowed"
        self.dt = timestep

    def set_minimisation(self, steps_total:int, steps_steepest:int|None = None):
        """Changes the configuration to run a minimisation rather than a dynamics simulation

        Args:
            steps_total (int): Total number of minimisation steps
            steps_steepest (int | None, optional): Number of steepest descent steps to take before swapping to conjugate gradient. If None, it will be changed to steps_total/2. Defaults to None.
        """
        assert steps_total >= 0, f"ERROR: Cannot run for negative steps, ({steps_total} not allowed)"
        if steps_steepest is None:
            steps_steepest = int(steps_total/2)
        self.imin = 1
        self._minimisation = True
        self.ncyc = steps_steepest
        self.maxcyc = steps_total

    def set_dynamics(self, timestep:float=0.002, shake:int=1):
        """Changes the configuration to run a dynamics simulation
        
        Args:
            timestep (float, optional): Timestep to use for dynamics simulation. Defaults to 2 ps.
            shake (int, optional): The nct configuration to use. 1 = no shake, 2 is restrain X-H bonds, 3 is shake all bonds. Defaults to 1.
        """
        self.imin = 0
        self._minimisation = False
        self.dt = timestep
        self.nct = shake
        if self._check_timestep_compatibility() == False:
            self.nct = 2
        
    def _check_timestep_compatibility(self)->bool:
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


    
    
    def _update_timestep(self, timestep:float=0.002):
        self.dt = timestep

    def to_dict(self)->dict:
        """Returns a dictionary of the class attributes"""
        return {key:value for key, value in vars(self).items() if not key.startswith('_')}
    
    def set_outputs(self, energy:int, restart:int, trajectory:int):
        """Sets the output frequencies for the calculation. 

        Args:
            energy (int): how frequently to print the energy (and other associated values)
            restart (int): how frequently to update the restart coordinates
            trajectory (int): how frequently to write to the trajectory file
        """
        self.ntpr = energy
        self.ntwr = restart
        self.ntwx = trajectory

    def set_restraints(self, restraint_mask:str, restraint_wt:float):
        """
        Allows for simple restraints using ambers selection algebra

        Args:
            restraint_mask (str): Atom selection
            restraint_wt (float, optional): Harmonic restraint weight. Defaults to 5.0.
        """
        if restraint_mask is not None:
            self.ntr = 1
            self.restraintmask = restraint_mask
            self.restraint_wt = restraint_wt
        else:
            self.ntr = 0
            try:
                self.restraintmask
            except NameError:
                del self.restraintmask

            
            try:
                self.restraint_wt
            except NameError:
                del self.restraint_wt


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