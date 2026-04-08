import os
import shutil
import subprocess
import time
import platform

from pymd.qm.qm import QM
from pymd.tools.structure import Molecule
from pymd.tools import io


class Orca(QM):
    """Orca QM Calculation class.

    Attributes:
        grid (str): The Keyword for the DFT grid.
        convergence_criteria (str): The keyword for the convergence criteria.
        print_level (str): The print level for the orca calculation.
        _primary_jobtype (str): What type of QM calculation to run.
        dispersion (str): The dispersion correction for the calculation.
        _out_file (list[str]): The contents of the output file.
        _energies (list[str]): The energies of each structure generated in the calculation.
        _secondary_frequency (str): Whether to run a frequency calculation after an optimisation
            calculation.
    """
    _binary: str|None = shutil.which("orca")
    grid: str
    convergence_criteria: str
    convergence_difficulty: str
    grid: str
    print_level: str
    _primary_jobtype: str = ""
    dispersion: str
    _subprocess_out: subprocess.CompletedProcess
    _out_file: list[str]
    _energies: list[float]
    _secondary_frequency: str = "None"

    def __init__(self, input_file_name: str,
            output_file_name: str|None,
            coordinates: str|Molecule,
            charge: int = 0,
            spin: int = 0,
            path: str = "./") -> None:
        """Initialises the QM Calculation.
        
        Args:
            input_file_name (str): Name of the input file. This should end in .inp
            output_file_name (str|None): Name of the output file. 
                If None, defaults to the name of the input file.
            coordinates (str|Molecule): The atomic coordinates for the system.
            charge (int): The net charge of the system.
            spin (int): The spin of the system.
            path (str): Where to run the calculation. Defaults to `./`.
        """
        if output_file_name is None:
            output_file_name = input_file_name.replace(".inp", ".out")
        super().__init__(input_file_name=input_file_name, output_file_name=output_file_name,
                         coordinates=coordinates, charge=charge, spin=spin, run_path=path)

    def get_commands(self) -> list[str]:
        """Returns a list of variables from the class attributes"""
        return [value for key, value in vars(self).items() if not key.startswith('_')]

    def add_job_variables(self, variable: str) -> None:
        """Adds a variable to the class attributes

        Args:
            variable (str): The Variable to add.
        """
        setattr(self, variable, variable)

    def set_conv_criteria(self, conv: str) -> None:
        """Sets the convergence criteria for the calculation
        
        Args:
            conv (str): Convergence criteia to be used. Options are as follows:
                ["sloppy", "loose", "medium", "strong", "tight", "verytight", "extreme"]
        """
        
        #TODO allow for checking of allowed convergence critera.
        # Also allow for defined convergence criteria.

    def build(self) -> None:
        """Builds the input file for the calculation. It sets up the _input_file attribute."""
        lines = []
        if self._dispersion is not None:
            self.dispersion = self._dispersion
        top_line = f"!{self._method} {self._basis} {self._primary_jobtype}"
        for cmd in self.get_commands():
            top_line += f" {cmd}"
        lines.append(top_line)
        if self._secondary_frequency != "None":
            lines.append(f"! {self._secondary_frequency}")
        lines.append(f"%PAL NPROCS {self._cores} END")
        lines.append(f"%MAXCORE {self._mem_per_core}")
        if self._input_coordinate_file is not None:
            lines.append(f"* xyzfile {self._input_coordinates.charge} " \
                + f"{self._input_coordinates.spin + 1} {self._input_coordinate_file}")
        elif isinstance(self._input_coordinates, Molecule):
            lines.append(f"* xyz {self._input_coordinates.charge} " \
                + f"{self._input_coordinates.spin + 1}\n{self._input_coordinates.print_coords()}*")
        else:
            raise AttributeError
        self._input_file = lines

    def run(self) -> None:
        """Builds the input file and runs Orca."""
        self.build()
        io.text_dump(text=self._input_file,
                    path=os.path.join(self._run_path, self._input_file_name))
        print("INFO: Running Orca...")
        

        start = time.perf_counter()
        with open(file=os.path.join(self._run_path, self._output_file_name), 
                  mode="w", encoding="utf-8") as f:
            if platform.system() == "Linux":
                # print(f"{self._binary} {self._input_file_name} '--bind-to hwthread' > " \
                #     + f"{self._output_file_name}")
                # output = subprocess.run(args=[self._binary, self._input_file_name,
                            # "'--bind-to hwthread'"], cwd=self._run_path, stdout=f, check=True)
                print(f"{self._binary} {self._input_file_name} > {self._output_file_name}")
                output = subprocess.run(args=[self._binary, self._input_file_name], cwd=self._run_path, stdout=f, stderr=f, check=True)  #TODO Fix this...  
            else:
                print(f"{self._binary} {self._input_file_name} > {self._output_file_name}")
                output = subprocess.run(args=[self._binary, self._input_file_name],
                                        cwd=self._run_path, stdout=f, stderr=f, check=True)
        stop = time.perf_counter()
        self._calculation_time = stop - start
        self._subprocess_out = output
        self._get_output_file()
        self._get_energies()


    def _get_output_file(self) -> None:
        """Reads the output file and stores it."""
        self._out_file = io.text_read(path=os.path.join(self._run_path,self._output_file_name))

    def _get_energies(self) -> None:
        """Gets the energies of all structures in the calculation. This should be a list of 
        length one if a single point calculation."""
        energies = []
        for line in self._out_file:
            if "FINAL SINGLE POINT ENERGY" in line:
                energies.append(float(line.split()[4]))
        self._energies = energies

    def print_output(self)->None:
        """Prints a custom output summary."""
        if len(self._energies) == 1:
            print(f"INFO: Calculated energy is {self._energies[0]} eh, calculation " \
                + f"time was {self._calculation_time} seconds")
        elif len(self._energies) > 1:
            print(f"INFO: Calculated initial energy was {self._energies[0]} eh")
            print(f"INFO: Calculated final energy was {self._energies[-1]} eh")
            print(f"INFO: Calculation time was {self._calculation_time} seconds")

    def add_solvent(self, solvent: str = "water", model: str = "CPCM") -> None:
        """Adds a implicit solvent to the calculation.
        
        Args:
            solvent (str): The solvent to use. Defaults to water.
            model (str): The implicit solvent modeul to use. Defaults to CPCM.
        """
        self.add_job_variables(variable=f"{model}({solvent})")

    def run_secondary_frequency(self, freq_type: str = "analytical") -> None:
        """Runs a frequency calculation after an optimisation calculation
        
        Args:
            freq_type (str): What type of frequency to calculate. Either Analytical or numerical. 
                Defuaults to Analytical
        """
        if freq_type == "numerical":
            self._secondary_frequency = "NumFreq"
        elif freq_type == "analytical":
            self._secondary_frequency = "AnFreq"
        else:
            self._secondary_frequency = "Freq"