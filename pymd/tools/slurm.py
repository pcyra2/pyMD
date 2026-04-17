"""
#TODO
"""
import time
import os
from pymd.tools.hpc import HPC, PartitionClass
from pymd.user_configs.hpc_defaults import DEFAULT_HPC

SLURM_STATUS_DICT = dict(R = "running",
                         CG = "completing",
                         CD = "completed",
                         F = "failed",
                         PD = "pending",
                         S = "suspended",
                         ST = "stopped")



class SlurmJob:
    """
    #TODO
    """
    job_id: int
    wall_time: float
    status: str
    name: str

    def __init__(self, name: str, job_id: int) -> None:
        """
        #TODO

        Args:
            name (str): _description_
            job_id (int): _description_
        """
        self.name = name
        self.job_id = job_id

    def add_wall_time(self, wall_time: float) -> None:
        """
        #TODO

        Args:
            wall_time (float): _description_
        """
        self.wall_time = wall_time

    def update_status(self, slurm_status: str) -> None:
        """
        #TODO

        Args:
            slurm_status (str): _description_
        """
        self.status = SLURM_STATUS_DICT[slurm_status]

class Slurm:
    """Contains information for a slurm job. This allows for checking that the 
    configuration is allowed. 

    Attributes:
        hpc (HPC): HPC to use
        partition (PartitionClass): Partition to use
        time (int): Job Wall time in hours
        name (str): Name of the job
        nodes (int): Number of nodes to use
        mem (int): Memory per node in GB
        gpus (int): Number of gpus to use
        modules (list[str]): Modules to load using the "modules system"
        array (bool): Whether to use an array job
        array_len (int):
        array_file (str): File to use for the array job
        tasks_pn (int): slurm NTASKS_PER_NODE variable
    """
    hpc: HPC = DEFAULT_HPC
    partition: PartitionClass  = DEFAULT_HPC.partitions["defq"]
    wall_time = 24
    name = "pyMD"
    nodes = 1
    mem = 10
    gpus = 0
    modules: list[str] = []
    array: bool = False
    array_len: int
    array_file: str|None = None
    tasks_pn: int
    job: SlurmJob
    hpc_run_dir: str
    local_file_dir: str
    file_name: str = "sub.sh"
    wait: bool = False
    ping_time: int = 60
    dependency: int|None = None

    def __init__(self,partition:str = "defq") -> None:
        """Initializes the job, by first selecting the partition
        
        Args:
            partition (str, optional): Partition to use. Defaults to defq.
        """
        assert partition in self.hpc.partitions.keys(), \
            f"Partition {partition} not recognized for HPC {self.hpc.name}."
        self.partition = HPC.partitions[partition]


    def __str__(self) -> str:
        return f"{self.name} SLURM JOB on {self.hpc.name} on {self.partition}"


    def set_time(self, wall_time:int) -> None:
        """Sets the maximum ammount of time for the slurm job. 

        Args:
            wall_time (int): Maximum time for the slurm job.
        """
        assert wall_time <= self.partition.wall_time, \
            f"Time {wall_time} exceeds max walltime for partition {self.partition} on HPC {self.hpc}."
        self.wall_time = wall_time


    def set_name(self, name:str) -> None:
        """Defines the job name

        Args:
            name (str): name of the job.
        """
        self.name = name


    def set_nodes(self, nodes:int) -> None:
        """Sets the number of nodes to use in the job.

        Args:
            nodes (int): Number of nodes to use
        """
        assert nodes <= self.partition.nodes, \
            f"Nodes {nodes} exceeds max nodes for partition {self.partition} on HPC {self.hpc}."
        self.nodes = nodes


    def set_mem(self, mem:int) -> None:
        """Allocates the memory for the job.

        Args:
            mem (int): Memory to allocate for the job in GB.
        """
        assert mem <= self.partition.mem_per_node, \
            f"Memory {mem} exceeds max memory for partition {self.partition} on HPC {self.hpc}."
        self.mem = mem


    def set_gpus(self, gpus:int) -> None:
        """Allocates the number of GPUs for the job

        Args:
            gpus (int): Number of GPU's for the job.
        """
        assert gpus <= self.partition.gpus_per_node, \
        	f"GPUs {gpus} exceeds max GPUs for partition {self.partition} on HPC {self.hpc}."
        self.gpus = gpus


    def set_modules(self, modules:list[str]) -> None:
        """Allocates the modules that are required for the job

        Args:
            modules (list[str]): List of modules to be loaded for the job. #TODO Add a way to 
            	define modules that are available on the HPC.
        """
        self.modules = modules


    def set_ntasks(self, tasks:int, per_node:bool = True) -> None:
        """Allocates the SLURM_NTASKS for the job

        Args:
            tasks (int): Number of tasks for the job.
            per_node (bool, optional): Whether to set the SLURM_NTASKS_PER_NODE for the job. 
            	Defaults to True. #TODO implement False
        """
        if per_node:
            self.tasks_pn = tasks
        else:
            raise NotImplementedError("Setting total tasks not implemented yet.")
        self.tasks_pn = tasks


    def set_array(self, array_file:str, length: int|None = None, check:bool = True) -> None:
        """Enables the use of array jobs
        
        Args:
            array_file (str): Path to file where each line is a job.
            length (int|None): The length of the array job. If None, the length is 
            	determined from the array file. 
            check (bool): Whether to check if the array file exists. Defaults to True.
            """
        if check:
            assert os.path.isfile(path=array_file), f"Array file {array_file} not found."
        self.array = True
        if length is None:
            with open(file=array_file, mode="r", encoding="UTF-8") as f:
                lines = f.readlines()
            self.array_len = len(lines)
        else:
            self.array_len = length
        self.array_file = array_file

    def add_dependency(self, dependency:int):
        self.dependency = dependency

    def gen_script(self, command:str)->str:
        """Generates the SLURM script for the job.

        Args:
            command (str): The command to run. 
        
        Returns:
            str: The SLURM file
        """
        file = f"""#!/bin/bash
#SBATCH --job-name={self.name}
#SBATCH --partition={self.partition.name}
#SBATCH --nodes={self.nodes}
#SBATCH --time={self.wall_time}:00:00
#SBATCH --mem={self.mem}GB
#SBATCH --ntasks-per-node={self.tasks_pn}"""
        if self.partition.qos is not None:
            file += f"\n#SBATCH --qos={self.partition.qos}"
        if self.gpus > 0:
            file += f"\n#SBATCH --gres=gpu:{self.gpus}"
        if self.array is True:
            file += f"\n#SBATCH --array=1-{self.array_len}"
        if self.dependency is not None:
            file += f"\n#SBATCH --dependency=afterany:{self.dependency}"
        file += "\n\n"

        if self.modules:
            for module in self.modules:
                file += f"module load {module}\n"

        file += "\n"
        if self.array is True:
            file += f"ARRAY_FILE=\"{self.array_file}\"\n"
            file += "CMD=$(cat $ARRAY_FILE | head -n $(($SLURM_ARRAY_TASK_ID*1)) | tail -n 1)\n"
            file += "echo \"Running job: $SLURM_ARRAY_TASK_ID\"\n"
            file += "echo \"Command: $CMD\"\n"
            file += "eval $CMD \n"

        file += f"\n\n{command}\n"

        return file

    def define_dirs(self, local_file_path: str, hpc_file_path: str) -> None:
        """
        #TODO

        Args:
            local_file_path (str): _description_
            hpc_file_path (str): _description_
        """
        self.hpc_run_dir = hpc_file_path
        self.local_file_dir = local_file_path

    def wait_for_finish(self, wait: bool, ping_time: int = 60) -> None:
        self.wait = wait
        self.ping_time = ping_time

    def submit(self) -> None:
        """
        #TODO

        Args:
            wait_for_finish (bool, optional): _description_. Defaults to False.
            time_ping (int, optional): _description_. Defaults to 60.

        Returns:
            SlurmJob: _description_
        """
        
        self.hpc.sync(work_dir=self.local_file_dir, hpc_work_dir=self.hpc_run_dir, direction="forward")
        job_id = self.hpc.submit_slurm(path=self.hpc_run_dir, file=self.file_name)
        self.job = SlurmJob(name=self.name, job_id=job_id)
        if self.wait:
            start = time.perf_counter()
            stop = time.perf_counter()
            finished = False
            while finished is False:
                time.sleep(self.ping_time)
                self.job.update_status(slurm_status=self.hpc.check_slurm_status(slurm_id=job_id))
                print(f"INFO: Job status = {self.job.status}")
                if self.job.status == "completed":
                    stop = time.perf_counter()
                    finished = True
            self.job.wall_time = stop - start
            print(f"INFO: calculation took {self.job.wall_time} +- {self.ping_time} s")
