from pyMD.MD.kernels.AMBER import Amber

import os
import subprocess
import time
import copy

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
    GPU: bool = False

    def __init__(self, 
                inputfile_name: str,
                input_structure: str,
                outputfile_name:str,
                run_path: str = "./"
                ):
        self.inputfile_name = inputfile_name
        self.outputfile_name = outputfile_name
        self.complete = False
        self.input_structure = input_structure
        self.run_path = run_path

    def add_inputfile(self, inputfile: list[str]):
        """The inputfile as a list of lines

        Args:
            inputfile (list[str]): Input file as a list of lines.
        """
        self.inputfile = inputfile

    def add_kernel(self, config: Amber):
        """Adds the kernel object to allow for direct running.

        Args:
            config (Amber): Amber Kernel object.
        """
        self.kernel = copy.deepcopy(config)

    def add_run_lines(self, lines: list[str]|str):
        """Adds run-lines to the job. Not really necessary currently as I have the job.exe although could be useful later to save run-lines for slurm submission.

        Args:
            lines (list[str] | str): lines to run. Usually in a list of commands to parse to subprocess
        """
        if isinstance(lines, str):
            lines = lines.split()
        self.runline = lines

    def to_gpu(self):
        """Converts the job to a GPU job
        """
        self.GPU = True
    
    def to_cpu(self):
        """Swaps the job back to a CPU job
        """
        self.GPU = False

    def exe(self, GPU: bool|None = None):
        
        if GPU is not None and GPU == True:
            self.to_gpu()
        elif GPU is not None and GPU == False:
            self.to_cpu()

        self.runline = self.kernel._gen_runlines(input_file_name=self.inputfile_name, 
                                                input_structure_name=self.input_structure,
                                                output_file_name=self.outputfile_name, 
                                                GPU=self.GPU)

        start = time.perf_counter()
        self.kernel.exec(self.inputfile_name, self.outputfile_name, self.input_structure, self.run_path, self.GPU)        
        stop = time.perf_counter()
        self.complete = True
        self.wall_time = stop - start