"""
#TODO
"""
import os
import time
import copy

from pymd.md.kernels.amber import Amber


class MDJobClass:
    """
    #TODO
    """
    inputfile: list[str]
    inputfile_name: str
    outputfile_name: str
    input_structure: str
    run_line: str|list[str]
    run_path: str
    complete: bool = False
    kernel: Amber
    wall_time: float
    gpu: bool = False


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
        """Adds run-lines to the job. Not really necessary currently as I have the job.exe 
            although could be useful later to save run-lines for slurm submission.

        Args:
            lines (list[str] | str): lines to run. Usually in a list of commands to parse to 
                subprocess
        """
        if isinstance(lines, str):
            lines = lines.split()
        self.run_line = lines


    def to_gpu(self):
        """Converts the job to a GPU job
        """
        self.gpu = True


    def to_cpu(self):
        """Swaps the job back to a CPU job
        """
        self.gpu = False


    def exe(self, gpu: bool|None = None):
        """
        #TODO

        Args:
            GPU (bool | None, optional): _description_. Defaults to None.
        """
        if gpu is not None and gpu is True:
            self.to_gpu()
        elif gpu is not None and gpu is False:
            self.to_cpu()

        self.run_line = self.kernel._gen_runlines(input_file_name=self.inputfile_name, 
                                                input_structure_name=self.input_structure,
                                                output_file_name=self.outputfile_name, 
                                                gpu=self.gpu)
        if self.gpu:
            if os.path.isfile(self.kernel.config.GPUPath) is False:
                assert os.path.isfile(self.kernel.config.CPUPath)
                self.to_cpu()
        else:
            assert os.path.isfile(self.kernel.config.CPUPath)

        start = time.perf_counter()
        self.kernel.exec(input_file_name=self.inputfile_name,
                        output_file_name=self.outputfile_name,
                        input_structure_name=self.input_structure,
                        path=self.run_path,
                        gpu=self.gpu)  
        stop = time.perf_counter()
        self.complete = True
        self.wall_time = stop - start
