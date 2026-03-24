import os 

class partitionClass:
    """
    Defines the default data for a HPC SLURM partition.
        
    Attributes:
        name (str): Name of the partition. 
        cpus_per_node (int): Maximum number of CPUs on a node.
        gpus_per_node (int): Maximum number of GPUs on a node.
        mem_per_node (int): Maximum ammount of RAM per node in GB.
        nodes (int): Maximum number of nodes in partition.
        walltime (int): Maximum ammount of time allowed in the partition in hours.
        qos (str|None): Quality of Service if required. Defaults to None.
    """
    cpus_per_node: int
    mem_per_node: int
    gpus_per_node: int
    nodes: int
    walltime: int
    qos: str|None
    name: str

    def __init__(self, name: str, 
                cpus_per_node: int, 
                gpus_per_node: int, 
                mem_per_node: int,
                nodes: int, 
                walltime: int,
                qos: str|None = None) -> None:
        """Defines the default data for a HPC SLURM partition.
        
        Args:
            name (str): Name of the partition. 
            cpus_per_node (int): Maximum number of CPUs on a node.
            gpus_per_node (int): Maximum number of GPUs on a node.
            mem_per_node (int): Maximum ammount of RAM per node in GB.
            nodes (int): Maximum number of nodes in partition.
            walltime (int): Maximum ammount of time allowed in the partition in hours.
            qos (str|None): Quality of Service if required. Defaults to None.
        """
        self.name = name
        self.cpus_per_node = cpus_per_node
        self.gpus_per_node = gpus_per_node
        self.mem_per_node = mem_per_node
        self.nodes = nodes
        self.walltime = walltime
        self.qos = qos

    def __str__(self) -> str:
        return f"Partition: {self.name}"


class HPC:
    """Defines a HPC cluster. This class contains all important information to how it is setup. 

    Attributes:
        partitions (dict[str,partitionClass]): Dictionary of all partitions
        login_node (str): Hostname of the HPC
        name (str): Name of the HPC
        username (str): Username to connect to the HPC
    """
    partitions: dict[str,partitionClass] = dict()
    login_node: str
    name: str
    username: str

    def __init__(self, name: str, login_node: str, username: str = os.getlogin()) -> None:
        """Initialises the HPC class. This allows allocation of name and how to connect

        Args:
            name (str): Name of the HPC
            login_node (str): Hostname of the HPC. (How to connect)
            username (str, optional): username to connect to the HPC. Defaults to the current username.
        """
        self.name = name
        self.login_node = login_node
        self.username = username


    def __str__(self) -> str:
        return f"HPC: {self.name}"


    def add_partition(self, partition: partitionClass) -> None:
        """Adds partitions to the HPC.

        Args:
            partition (partitionClass): Partition to add
        """
        self.partitions[partition.name] = partition


ADA = HPC(name="ada", login_node="hpclogin02.ada.nottingham.ac.uk")
ADA.add_partition(partitionClass("q4bioq", 96, 8, 1900, 1, 672, "q4bio" ))
ADA.add_partition(partitionClass("defq", 96, 0, 361, 63, 168))
ADA.add_partition(partitionClass("ampereq", 96, 8, 747, 3, 168))
ADA.add_partition(partitionClass("ampere-mq", 96, 56, 747, 1, 168))
ADA.add_partition(partitionClass("compchemq", 56, 4, 384, 5, 168, "compchem"))



class slurm:
    """Contains information for a slurm job. This allows for checking that the configuration is allowed. 

    Attributes:
        hpc (HPC): HPC to use
        partition (partitionClass): Partition to use
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
    hpc: HPC = ADA
    partition: partitionClass  = ADA.partitions["defq"]
    time = 24
    name = "pyMD"
    nodes = 1
    mem = 10
    gpus = 0
    modules: list[str]
    array: bool = False
    array_len: int
    array_file: str|None = None
    tasks_pn: int

    def __init__(self,partition:str = "defq"):
        """Initialises the job, by first selecting the partition
        
        Args:
            partition (str, optional): Partition to use. Defaults to defq.
        """
        assert partition in self.hpc.partitions.keys(), f"Partition {partition} not recognised for HPC {self.hpc.name}."
        self.partition = HPC.partitions[partition]


    def __str__(self) -> str:
        return f"{self.name} SLURM JOB on {self.hpc.name} on {self.partition}"

    def set_time(self, time:int):
        """Sets the maximum ammount of time for the slurm job. 

        Args:
            time (int): Maximum time for the slurm job.
        """
        assert time <= self.partition.walltime, f"Time {time} exceeds max walltime for partition {self.partition} on HPC {self.hpc}."
        self.time = time


    def set_name(self, name:str):
        """Defines the job name

        Args:
            name (str): name of the job.
        """
        self.name = name


    def set_nodes(self, nodes:int):
        """Sets the number of nodes to use in the job.

        Args:
            nodes (int): Number of nodes to use
        """
        assert nodes <= self.partition.nodes, f"Nodes {nodes} exceeds max nodes for partition {self.partition} on HPC {self.hpc}."
        self.nodes = nodes


    def set_mem(self, mem:int):
        """Allocates the memory for the job.

        Args:
            mem (int): Memory to allocate for the job.
        """
        assert mem <= self.partition.mem_per_node, f"Memory {mem} exceeds max memory for partition {self.partition} on HPC {self.hpc}."
        self.mem = mem


    def set_gpus(self, gpus:int):
        """Allocates the number of GPUs for the job

        Args:
            gpus (int): Number of GPU's for the job.
        """
        assert gpus <= self.partition.gpus_per_node, f"GPUs {gpus} exceeds max GPUs for partition {self.partition} on HPC {self.hpc}."
        self.gpus = gpus


    def set_modules(self, modules:list[str]):
        """Allocates the modules that are required for the job

        Args:
            modules (list[str]): List of modules to be loaded for the job. #TODO Add a way to define modules that are available on the HPC.
        """
        self.modules = modules


    def set_ntasks(self, tasks:int, per_node:bool = True):
        """Allocates the SLURM_NTASKS for the job

        Args:
            tasks (int): Number of tasks for the job.
            per_node (bool, optional): Whether to set the SLURM_NTASKS_PER_NODE for the job. Defaults to True. #TODO implement False
        """
        if per_node:
            self.tasks_pn = tasks
        else:
            raise NotImplementedError("Setting total tasks not implemented yet.")
        self.tasks_pn = tasks


    def set_array(self, array_file:str, length: int|None = None, check:bool = True):
        """Enables the use of array jobs
        
        Args:
            array_file (str): Path to file where each line is a job.
            length (int|None): The length of the array job. If None, the length is determined from the array file. 
            check (bool): Whether to check if the array file exists. Defaults to True.
            """
        if check:
            assert os.path.isfile(array_file), f"Array file {array_file} not found."
        self.array = True
        if length is None:
            with open(array_file, "r") as f:
                lines = f.readlines()
            self.array_len = len(lines)
        else:
            self.array_len = length
        self.array_file = array_file


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
#SBATCH --time={self.time}:00:00
#SBATCH --mem={self.mem}GB
#SBATCH --ntasks-per-node={self.tasks_pn}"""
        if self.partition.qos is not None:
            file += f"\n#SBATCH --qos={self.partition.qos}"
        if self.gpus > 0:
            file += f"\n#SBATCH --gres=gpu:{self.gpus}"
        if self.array == True:
            file += f"\n#SBATCH --array=1-{self.array_len}"
        file += "\n\n"
        
        if self.modules:
            for module in self.modules:
                file += f"module load {module}\n"
       
        file += "\n"
        if self.array == True:
            file += f"ARRAY_FILE=\"{self.array_file}\"\n"
            file += f"CMD=$(cat $ARRAY_FILE | head -n $(($SLURM_ARRAY_TASK_ID*1)) | tail -n 1)\n"
            file += f"echo \"Running job: $SLURM_ARRAY_TASK_ID\"\n"
            file += f"echo \"Command: $CMD\"\n"
            file += f"eval $CMD \n"
        
        file += f"\n\n{command}\n"

        return file