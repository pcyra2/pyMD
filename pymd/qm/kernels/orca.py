import os
import shutil
import subprocess
import time
import platform

from pymd.qm.qm import QM
from pymd.tools.structure import Molecule
from pymd.tools import io


class Orca(QM):
    _binary: str = shutil.which("orca")
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

    def __init__(self, input_file_name: str, output_file_name: str|None, coordinates: str|Molecule,
                path: str = "./") -> None:
        if output_file_name is None:
            output_file_name = input_file_name.replace(".inp", ".out")
        super().__init__(input_file_name=input_file_name, output_file_name=output_file_name,
                         coordinates=coordinates, run_path=path)

    def get_commands(self) -> list[str]:
        """Returns a list of variables from the class attributes"""
        return [value for key, value in vars(self).items() if not key.startswith('_')]

    def add_job_variables(self, variable: str) -> None:
        setattr(self, variable, variable)

    def set_conv_criteria(self, conv: str) -> None:
        """Sets the convergence criteria for the calculation"""
        self.add_job_variables(f"{conv.capitalize()}SCF") 
        #TODO allow for checking of allowed convergence critera.
        # Also allow for defined convergence criteria.

    def build(self) -> None:
        lines = []
        if self._dispersion is not None:
            self.dispersion = self._dispersion
        top_line = f"!{self._method} {self._basis} {self._primary_jobtype}"
        for cmd in self.get_commands():
            top_line += f" {cmd}"
        lines.append(top_line)
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
        self.build()
        io.text_dump(text=self._input_file,
                    path=os.path.join(self._run_path, self._input_file_name))
        print("Running Orca...")
        

        start = time.perf_counter()
        with open(file=os.path.join(self._run_path, self._output_file_name), 
                  mode="w", encoding="utf-8") as f:
            if platform.system() is "Linux":
                print(f"{self._binary} {self._input_file_name} '--bind-to hwthread' > " \
                    + f"{self._output_file_name}")
                output = subprocess.run(args = [self._binary, self._input_file_name, 
                            "'--bind-to hwthread'"], cwd=self._run_path, stdout=f, check=True)
            else:
                print(f"{self._binary} {self._input_file_name} > {self._output_file_name}")
                output = subprocess.run(args = [self._binary, self._input_file_name], 
                                        cwd=self._run_path, stdout=f, check=True)
        stop = time.perf_counter()
        self._calculation_time = stop - start
        self._subprocess_out = output
        self._get_output_file()
        self._get_energies()


    def _get_output_file(self) -> None:
        self._out_file = io.text_read(path=os.path.join(self._run_path,self._output_file_name))

    def _get_energies(self):
        energies = []
        for line in self._out_file:
            if "FINAL SINGLE POINT ENERGY" in line:
                energies.append(float(line.split()[4]))
        self._energies = energies

    def print_output(self)->None:
        if len(self._energies) == 1:
            print(f"INFO: Calculated energy is {self._energies[0]} eh, calculation " \
                + f"time was {self._calculation_time} seconds")
        elif len(self._energies) > 1:
            print(f"INFO: Calculated initial energy was {self._energies[0]} eh")
            print(f"INFO: Calculated final energy was {self._energies[-1]} eh")
            print(f"INFO: Calculation time was {self._calculation_time} seconds")