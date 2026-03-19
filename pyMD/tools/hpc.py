import os 

class partitionClass:
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
        self.name = name
        self.cpus_per_node = cpus_per_node
        self.gpus_per_node = gpus_per_node
        self.mem_per_node = mem_per_node
        self.nodes = nodes
        self.walltime = walltime
        self.qos = qos


class HPC:
    partitions: dict = dict()
    login_node: str
    name: str
    
    def __init__(self, name: str, login_node: str) -> None:
        self.name = name
        self.login_node = login_node

    def add_partition(self, partition: partitionClass) -> None: 
        self.partitions[partition.name] = partition


ADA = HPC(name="ada", login_node="hpclogin02.ada.nottingham.ac.uk")
ADA.add_partition(partitionClass("q4bioq", 96, 8, 1900, 1, 672, "q4bio" ))
ADA.add_partition(partitionClass("defq", 96, 0, 361, 63, 168))
ADA.add_partition(partitionClass("ampereq", 96, 8, 747, 3, 168))
ADA.add_partition(partitionClass("ampere-mq", 96, 56, 747, 1, 168))
ADA.add_partition(partitionClass("compchemq", 56, 4, 384, 5, 168, "compchem"))



class slurm:
    hpc: HPC = ADA
    partition: partitionClass  = ADA.partitions["defq"]
    time = 24
    name = "Submission"
    nodes = 1
    mem = 10
    gpus = 0
    modules: list[str]
    array: bool = False
    array_len: int
    array_file: str
    tasks_pn: int

    def __init__(self,partition:str = "defq"):
        assert partition in self.hpc.partitions.keys(), f"Partition {partition} not recognised for HPC {self.hpc.name}."
        self.partition = HPC.partitions[partition]


    def set_time(self, time:int):
        assert time <= self.partition.walltime, f"Time {time} exceeds max walltime for partition {self.partition} on HPC {self.hpc}."
        self.time = time


    def set_name(self, name:str):
        self.name = name


    def set_nodes(self, nodes:int):
        assert nodes <= self.partition.nodes, f"Nodes {nodes} exceeds max nodes for partition {self.partition} on HPC {self.hpc}."
        self.nodes = nodes


    def set_mem(self, mem:int):
        assert mem <= self.partition.mem_per_node, f"Memory {mem} exceeds max memory for partition {self.partition} on HPC {self.hpc}."
        self.mem = mem


    def set_gpus(self, gpus:int):
        assert gpus <= self.partition.gpus_per_node, f"GPUs {gpus} exceeds max GPUs for partition {self.partition} on HPC {self.hpc}."
        self.gpus = gpus


    def set_modules(self, modules:list[str]):
        self.modules = modules


    def set_ntasks(self, tasks:int, per_node:bool = True):
    
        if per_node:
            self.tasks_pn = tasks
        else:
            raise NotImplementedError("Setting total tasks not implemented yet.")
        self.tasks_pn = tasks


    def set_array(self, array_file:str, length: int|None = None, check:bool = True):
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


    def gen_script(self, command:str = "")->str:
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