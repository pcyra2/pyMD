import os
import shutil
import subprocess
import time
import platform

from pymd.qm.qm import QM
from pymd.tools.structure import Molecule
from pymd.tools import io


class Gaussian(QM):
    """Gaussian QM Calculation class.

    Attributes:
        _binary (str|None): The path to the gaussian executable.
        grid (str): The Keyword for the DFT grid.
        convergence_criteria (str): The keyword for the convergence criteria.
        print_level (str): The print level for the gaussian calculation.
        _primary_jobtype (str): What type of QM calculation to run.
        dispersion (str): The dispersion correction for the calculation.
        _subprocess_out (str): The subprocess output.
        _out_file (list[str]): The contents of the output file.
        _energies (list[str]): The energies of each structure generated in the calculation.
        _secondary_frequency (str): Whether to run a frequency calculation after an optimisation
            calculation.
    """
    _binary: str|None = shutil.which("g16")
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
        raise NotImplementedError("Setting of convergence criteria not yet implemented for Gaussian. Please set this manually in the input file or use the default convergence criteria.")


    def build(self) -> None:
        """Builds the input file for the calculation. It sets up the _input_file attribute."""
        raise NotImplementedError("Setting of convergence criteria not yet implemented for Gaussian. Please set this manually in the input file or use the default convergence criteria.")

     

    def run(self) -> None:
        """Builds the input file and runs Gaussian."""
        self.build()
        io.text_dump(text=self._input_file,
                    path=os.path.join(self._run_path, self._input_file_name))
        print("INFO: Running Gaussian...")
        raise NotImplementedError("Setting of convergence criteria not yet implemented for Gaussian. Please set this manually in the input file or use the default convergence criteria.")


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
        raise NotImplementedError("Energy parsing not yet implemented for Gaussian. Please parse the output file manually.")
        # energies = []
        # for line in self._out_file:
        #     if "FINAL SINGLE POINT ENERGY" in line:
        #         energies.append(float(line.split()[4]))
        # self._energies = energies

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
        raise NotImplementedError("Setting of convergence criteria not yet implemented for Gaussian. Please set this manually in the input file or use the default convergence criteria.")

        # self.add_job_variables(variable=f"{model}({solvent})")

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