"""
#TODO
"""
import os
import time
import copy

from pymd.md.kernels.amber import Amber
from pymd.tools.slurm import Slurm
from pymd.tools import io


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
    hpc: Slurm|None = None

    def __init__(self,
                inputfile_name: str,
                input_structure: str,
                outputfile_name:str,
                run_path: str = "./"
                ) -> None:
        """
        #TODO

        Args:
            inputfile_name (str): _description_
            input_structure (str): _description_
            outputfile_name (str): _description_
            run_path (str, optional): _description_. Defaults to "./".
        """
        self.inputfile_name = inputfile_name
        self.outputfile_name = outputfile_name
        self.complete = False
        self.input_structure = input_structure
        self.run_path = run_path


    def add_inputfile(self, inputfile: list[str]) -> None:
        """The inputfile as a list of lines

        Args:
            inputfile (list[str]): Input file as a list of lines.
        """
        self.inputfile = inputfile


    def add_kernel(self, config: Amber) -> None:
        """Adds the kernel object to allow for direct running.

        Args:
            config (Amber): Amber Kernel object.
        """
        self.kernel = copy.deepcopy(x=config)


    def add_run_lines(self, lines: list[str]|str) -> None:
        """Adds run-lines to the job. Not really necessary currently as I have the job.exe 
            although could be useful later to save run-lines for slurm submission.

        Args:
            lines (list[str] | str): lines to run. Usually in a list of commands to parse to 
                subprocess
        """
        if isinstance(lines, str):
            lines = lines.split()
        self.run_line = lines


    def to_gpu(self) -> None:
        """Converts the job to a GPU job
        """
        self.gpu = True


    def to_cpu(self) -> None:
        """Swaps the job back to a CPU job
        """
        self.gpu = False

    def attach_slurm(self, hpc:Slurm) -> None:
        """
        #TODO

        Args:
            hpc (Slurm): _description_
        """
        self.hpc = hpc

    def exe(self, gpu: bool|None = None, hpc: Slurm|None = None) -> None:
        """
        #TODO

        Args:
            gpu (bool | None, optional): _description_. Defaults to None.
            hpc (Slurm | None, optional): _description_. Defaults to None.
        """
        if gpu is not None and gpu is True:
            self.to_gpu()
        elif gpu is not None and gpu is False:
            self.to_cpu()
        if hpc is not None:
            self.hpc = hpc

        if self.gpu:
            if os.path.isfile(path=self.kernel.config.GPUPath) is False:
                assert os.path.isfile(path=self.kernel.config.CPUPath)
                self.to_cpu()
        else:
            assert os.path.isfile(path=self.kernel.config.CPUPath)

        self.run_line = self.kernel._gen_runlines(
                            input_file_name=self.inputfile_name,
                            input_structure_name=self.input_structure,
                            output_file_name=self.outputfile_name,
                            gpu=self.gpu)
        if self.hpc is not None:
            assert self.run_line == self.hpc.local_file_dir, \
                "ERR: There is a mis-match between the cwd of the slurm object and the md job."

            ## Generate slurm submission script
            slurm_script = self.hpc.gen_script(command=self.run_line)
            io.text_dump(text=slurm_script, path=os.path.join(self.run_path, self.hpc.file_name))

            ## Sync the files, submit, and wait for end.
            self.hpc.submit(wait_for_finish=True)

            ## Sync the files back
            self.hpc.hpc.sync(work_dir=self.run_path, hpc_work_dir=self.hpc.hpc_run_dir, direction="backward")
            if self.hpc.job.status == "completed":
                self.complete = True
            self.wall_time = self.hpc.job.wall_time
        else:
            start = time.perf_counter()
            self.kernel.exec(input_file_name=self.inputfile_name,
                            output_file_name=self.outputfile_name,
                            input_structure_name=self.input_structure,
                            path=self.run_path,
                            gpu=self.gpu)
            stop = time.perf_counter()
            self.complete = True
            self.wall_time = stop - start
