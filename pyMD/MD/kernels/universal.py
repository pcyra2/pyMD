from pyMD.MD.kernels.AMBER import Amber

import os
import subprocess
import time

class MDJobClass:
    inputfile: list[str]
    inputfile_name: str
    outputfile_name: str
    input_structure: str
    runline: str|list[str]
    run_path: str
    complete: bool = False
    kernel: Amber
    wall_time: float

    def __init__(self, 
                inputfile_name: str,
                outputfile_name:str,
                run_path: str = "./"
                ):
        self.inputfile_name = inputfile_name
        self.outputfile_name = outputfile_name
        self.complete = False

    def add_inputfile(self, inputfile: list[str]):
        self.inputfile = inputfile

    def add_kernel(self, config: Amber):
        self.config = config

    def add_run_lines(self, lines: list[str]|str):
        if isinstance(lines, str):
            lines = lines.split()
        self.runline = lines

    def exe(self, GPU: bool = False):
        
        start = time.perf_counter()
        self.kernel.exec(self.inputfile_name, self.outputfile_name, self.input_structure)        
        stop = time.perf_counter()
        self.complete = True
        self.wall_time = stop - start