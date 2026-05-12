"""#TODO"""

from pymd.tools.structure import Molecule
from pymd.tools import io

class QM:
    """Base class for all QM calculations
    
    Attributes:
        _input_coordinate_file (str|None): The input coordinate file name. If None is passed in, 
            the coordinates will be printed in the input file from the `_input_coordinates` 
            molecule object.
        _input_file_name (str): The input file name.
        _output_file_name (str): The output file name. Defaults to `_input_file_name.out`.
        _input_coordinates (Molecule): The input coordinates in a Molecule object.
        _method (str): The QM method to be used for the QM calculation.
        _basis (str): The basis set to be used for the QM calculation.
        _dispersion (str|None): The dispersion correction to be used for the QM calculation.
        _input_file (str|list[str]): The contents of the input file that will be printed.
        _run_path (str): The directory to run the calculation in.
        _cores (int): The number of cores to be given to the calculation.
        _mem_total (int): The total amount of memory to be given to the claculation in MB.
            Defaults to 1000 MB (1GB).
        _mem_per_core (int): The amount of memory in MB to be given per core in the Calculation. 
            This defaults to 1GB and is used for ORCA calculations.
        _gpu (bool): Whether a the QM calculation can be run on GPU. Defaults to False.
        _charge (int): The net charge of the system.
        _spin (int): The spin of the system. This should be 2S not 2S+1.
        _calculation_time (float): The length of time the calculation took.
    """
    _input_coordinate_file: str|None = None
    _input_file_name: str
    _output_file_name: str
    _input_coordinates: Molecule
    _method: str
    _basis: str
    _dispersion: str|None = None
    _input_file: str|list[str]
    _run_path: str = "./"
    _cores: int = 1
    _mem_total: int = 1000
    _mem_per_core: int = 1000
    _gpu: bool = False
    _charge: int
    _spin: int
    _calculation_time: float


    def __init__(self,
            input_file_name: str,
            output_file_name: str,
            coordinates: Molecule|str,
            charge: int = 0,
            spin: int = 0,
            run_path: str = "./",
            cores: int = 1) -> None:
        """Initialises the QM Class
        
        Args:
            input_file_name (str): Name of the input file name for the QM calculation
            output_file_name (str): Name of the output file name for the QM Calculation
            coordinates (Molecule|str|list[str]): Coordinates of molecule to simulate. 
                Can be either a Molecule, a path to a ".xyz" or ".mol2" file.
            charge (int): Net charge of the system. Defaults to 0.
            spin (int): Spin of the system. (2S not 2S + 1). Defaults to 0.
            run_path (str): Path to run the calculation.
            cores (int): Number of CPU cores to run the calculation on. 
        """
        if isinstance(coordinates, Molecule):
            print("Molecule object passed as argument")
            self._input_coordinate_file = None
            self._input_coordinates = coordinates
            self._charge = charge
            self._spin = spin
        elif isinstance(coordinates, str):
            self._input_coordinate_file = coordinates
            crd_file = io.text_read(path=coordinates)
            if coordinates.endswith(".xyz"):
                mol = Molecule()
                mol.from_xyz(lines=crd_file, charge=charge, spin=spin)
                self._input_coordinates = mol
            elif coordinates.endswith(".mol2"):
                mol = Molecule()
                mol.from_mol2(lines=crd_file, charge=charge, spin=spin)
                self._input_coordinates = mol
        self._input_file_name = input_file_name
        self._output_file_name = output_file_name
        self.set_run_path(path=run_path)
        self._cores = cores
        self._charge = charge
        self._spin = spin


    def set_run_path(self, path: str) -> None:
        """Defines the path to run the QM calculation.
        
        Args:
            path (str): The path to run the calculation.
        """
        self._run_path = path


    def set_standard_variables(self, method: str, basis: str, disp: str|None = None) -> None:
        """A quick method to set all the standard variables for a calculation.

        Args:
            method (str): The QM method to use.
            basis (str): The QM basis set to use.
            disp (str|None): The dispersion correction to use if any. Defaults to None.
        """
        self.set_method(method=method)
        self.set_basis(basis=basis)
        if disp is not None:
            self.set_dispersion(disp=disp)


    def set_method(self, method: str) -> None:
        """The QM method to use.

        Args:
            method (str): The QM method to use.
        """
        self._method = method


    def set_basis(self, basis: str) -> None:
        """Sets the basis set to use.

        Args:
            basis (str): The basis set to use.
        """
        self._basis = basis


    def set_dispersion(self, disp: str) -> None:
        """Sets the dispersion correction to be used.
        
        Args:
            disp (str): The dispersion correction to use.
        """
        self._dispersion = disp


    def set_hardware(self, cores: int = 1, mem: int = 1000, gpu: bool = False) -> None:
        """Set hardware parameters for the calculation.
        
        Args:
            cores (int): Number of CPU cores to give the calculation.
            mem (int): Total memory in MB for the calculation.
            gpu (bool): Whether to use a GPU for the calculation (if available)
        """
        self._cores = cores
        self._mem_total = mem
        self._mem_per_core = int(mem/cores)
        self._gpu = gpu
        

    def set_cores(self, cores: int) -> None:
        """Sets the number of CPU cores to give to the calculation
        
        Args:
            cores (int): Number of cores to give.
        """
        self._cores = cores