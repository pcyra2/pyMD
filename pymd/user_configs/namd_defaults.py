"""#TODO
"""

from pymd.tools.convert import time


class NamdConfig:
    """
    Attributes:
        _CPUPath (str): path to the CPU executable
        _GPUPath (str): path to the GPU executable

        ## General options
        parmfile (str): parameter file.
        ambercoor (str): amber topology file for when using amber parameters/topologies.
        input (str): input structure name
        output (str): output file prefix

        ## IO options
        outputEnergies (int): Frequency to output the energy data
        restartfreq (int): Frequency to update the restart coordinates
        outputTiming (int): Frequency to print timing information
        DCDfreq (int): Frequency to write to the trajectory file
        DCDfile (str): File to write the trajectories to. Defaults to `${output}.dcd`.
        restartname (str): Name of the restart file. Defaults to `${output}.restart`.
        outputname (str): Name of the output file. Defaults to `${output}`

        ## Dynamics parameters
        timestep (float): Time step in femtoseconds. Defaults to 2 fs
        minimize (int): Number of minimisation steps
        seed (int): Random seed to use for the simulation
        run (int): Number of dynamics steps to run.

        ## Temperature parameters
        temperature (float): The temperature for the dynamics simulation
        reassignFreq (int): How frequently to change the temperature
        reassignIncr (float): How much to change the temperature by
        reassignHold (float): The temperature to stop heating at.
        langevinTemp (float): The temperature when running langevin dynamics
        langevinDamping (float): The langevin coupling constant (1/ps)

        ## Pressure options
        langevin (str): Whether to perform langevin dynamics. Options are `off` or `on`.
            Defaults to off.
        langevinPiston (str): whether to use Nose-Hoover Langevin pressure control. Defaults to on when NPT
        langevinPistonTarget (float): The target pressure for the Langevin piston in bar. Defaults to 1.013 bar
        langevinPistonPeriod (float): Oscilation time in fs for langevin piston. Default to 200 fs.
        LangevinPistonDecay (float): barostat dampening time scale in fs. make larger to reduce damping, smaller to increase. Defaults to 100 fs
        LangevinPistonTemp (float): The temperature of the system.

    """
    _CPUPath: str = ""
    _GPUPath: str = ""


    ## General options
    parmfile: str
    ambercoor: str
    input: str
    output: str


    ## IO options
    outputEnergies: int = 1
    restartfreq: int = 1
    outputTiming: int = 100
    DCDfreq: int = 1
    DCDfile: str = "${output}.dcd"
    restartname: str = "${output}.restart"
    outputname: str = "${output}"


    ## Dynamics parameters
    timestep: float = 2.0
    minimize: int
    seed: int = -1
    run: int


    ## Temperature parameters
    temperature: float = 300.0
    reassignFreq: int
    reassignIncr: float
    reassignHold: float
    langevinTemp: float = 300.0
    langevinDamping: float = 5
    


    ## Pressure options
    langevin: str = "off"
    langevinPiston: str = "on"
    langevinPistonTarget: float = 1.013
    langevinPistonPeriod: int = 200
    langevinPistonDecay: int = 100
    langevinPistonTemp: float = 300



    ## Restraint options
    rigidBonds: str = "all"
    rigidTolerance: float = 1.0e-8
    rigidIterations: int = 100


    ## Simulation parameters
    switching: str = "off"
    _1_4scaling: float =  0.833333333
    exclude: str = "scaled1-4"
    scnb: float = 2.0
    readexclusions: str =  "yes"
    pairListdist: int = 11
    LJcorrection: str =  "on"
    fullElectFrequency: int = 1
    nonBondedFreq: int = 1
    ZeroMomentum: str = "off"
    stepspercycle: int = 10
    cutoff: float = 10


    ## Forcefield information
    amber: str = "yes"
    watermodel: str = "tip3p"


    ## Cell definition
    _cell_shape: str = "oct"
    cellBasisVector1: str
    cellBasisVector2: str
    cellBasisVector3: str
    cellOrigin: str = "0 0 0"
    wrapNearest: str = "on"


    ## PME parameters
    PME: str = "on"
    PMEGridSizeX: int = 300
    PMEGridSizeY: int = 300
    PMEGridSizeZ: int = 300
    PMEInterpOrder: int = 4
    PMETolerance: float = 1.0e-6


    ## Extras
    GPUresident: str = "off"


    ## QM options
    qmForces: str = "off"
    qmlines: str = ""


    _minimisation: bool = False


    def __init__(self) -> None:
        pass


    def to_dict(self)->dict:
        """Returns a dictionary of the class attributes"""
        return {key:value for key, value in vars(self).items() if not key.startswith('_')}


    def set_timestep(self, timestep: float, units = "fs") -> None:
        assert timestep > 0, f"ERROR: Cannot have a negative timestep: {timestep} not allowed"
        self.timestep = timestep


    def set_minimisation(self, steps_total: int) -> None:
        assert steps_total > 0, "ERROR: Cannot have a negative number of minimisation steps."
        self.minimize = steps_total
        self._minimisation = True

    def set_dynamics(self, timestep: float, shake: str, timestep_units: str):
        self.set_timestep(timestep=timestep, units=timestep_units)
        assert shake in SHAKE_VARIABLES
        if shake != "none":
            self.rigidBonds = shake
            self.rigidIterations = self.rigidIterations
            self.rigidTolerance = self.rigidTolerance

    def set_outputs(self, energy: int, restart: int, trajectory: int):
        self.outputEnergies = energy
        self.outputTiming = energy
        self.DCDfreq = trajectory
        self.restartfreq = restart

    def _check_timestep_compatibility(self) -> bool:
        """Checks that the timestep and the shake are compatible with each other

        Returns:
            bool: True/False depending on compatibility
        """
        if self.rigidBonds == "None" and self.timestep < 1:
            return True
        elif self.rigidBonds == "all":
            return True
        else:
            return False
        
SHAKE_VARIABLES = ["none", "water", "all"]