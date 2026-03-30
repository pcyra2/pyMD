"""#TODO
"""
import os
import subprocess
from dataclasses import dataclass

@dataclass
class PartitionClass:
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
    wall_time: int
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
        self.wall_time = walltime
        self.qos = qos

    def __str__(self) -> str:
        return f"Partition: {self.name}"


class HPC:
    """Defines a HPC cluster. This class contains all important information to how it is setup. 

    Attributes:
        partitions (dict[str,PartitionClass]): Dictionary of all partitions
        login_node (str): Hostname of the HPC
        name (str): Name of the HPC
        username (str): Username to connect to the HPC
    """
    partitions: dict[str,PartitionClass] = dict()
    login_node: str
    name: str
    username: str

    def __init__(self, name: str, login_node: str, username: str|None = None) -> None:
        """Initializes the HPC class. This allows allocation of name and how to connect

        Args:
            name (str): Name of the HPC
            login_node (str): Hostname of the HPC. (How to connect)
            username (str, optional): username to connect to the HPC. 
            Defaults to the current username.
        """
        self.name = name
        self.login_node = login_node
        if username is None:
            try:
                self.username = os.getlogin()
            except OSError:
                print("WARN: Cannot find username. setting to the creators username :) => brara83")
                self.username = "brara83"
        else:
            self.username = username


    def __str__(self) -> str:
        return f"HPC: {self.name}"


    def add_partition(self, partition: PartitionClass) -> None:
        """Adds partitions to the HPC.

        Args:
            partition (partitionClass): Partition to add
        """
        self.partitions[partition.name] = partition

    def sync(self, work_dir: str, hpc_work_dir: str, direction: str = "forward"):
        """
        #TODO

        Args:
            work_dir (str): _description_
            hpc_work_dir (str): _description_
            direction (str, optional): _description_. Defaults to "forward".
        """
        if direction.casefold() == "forward":
            print(f"INFO: syncing {work_dir} to {self.login_node}:{hpc_work_dir}/.")
            print(f"INFO: Running command: rsync -azP {work_dir}* " \
                  + f"{self.username}@{self.login_node}:{hpc_work_dir}/. ")

            subprocess.run(["rsync", "-azP", f"{work_dir}/",
                            f"{self.username}@{self.login_node}:{hpc_work_dir}/."],
                            check=True)
            print("INFO: Data synced.")

        elif direction.casefold() == "backward":
            print(f"INFO: syncing {self.login_node}:{hpc_work_dir}/* to {work_dir}")
            print("INFO: Running command: rsync -azP " \
                  + f"{self.username}@{self.login_node}:{hpc_work_dir}/* .")
            subprocess.run(["rsync", "-azP",
                            f"{self.username}@{self.login_node}:{hpc_work_dir}/", "."],
                           cwd=work_dir, check=True)
            print("INFO: Data synced.")

    def _run_remote_command(self, command: str, error_check: bool = True) -> subprocess.CompletedProcess[str]:
        """
        #TODO

        Args:
            command (str): _description_
            error_check (bool, optional): _description_. Defaults to True.

        Returns:
            _type_: _description_
        """
        return subprocess.run(args=["ssh", f"{self.username}@{self.login_node}", command],
                       check=error_check, encoding="UTF-8",
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def remove_dir(self, hpc_work_dir: str) -> None:
        """
        #TODO

        Args:
            hpc_work_dir (str): _description_
        """
        print(f"INFO: deleting directory in `{hpc_work_dir}` on {self.name}")
        _ = self._run_remote_command(command=f"rm -r {hpc_work_dir}")


    def make_dir(self, hpc_work_dir: str) -> None:
        """
        #TODO

        Args:
            hpc_work_dir (str): _description_
        """
        print(f"INFO: Making directory `{hpc_work_dir}` on {self.name}")
        _ = self._run_remote_command(command=f"mkdir {hpc_work_dir}", error_check=False)


    def submit_slurm(self, path: str, file: str) -> int:
        """
        #TODO

        Args:
            path (str): _description_
            file (str): _description_

        Returns:
            int: _description_
        """
        print(f"INFO: Submitting slurm job {file} from {path}")
        output = self._run_remote_command(command=f"cd {path} ; sbatch {file}")
        stdout = output.stdout
        print(f"INFO: Job ID is {stdout.split()[-1]}")
        return int(stdout.split()[-1])


    def check_slurm_status(self, slurm_id: int) -> str:
        """
        #TODO

        Args:
            slurm_id (int): _description_

        Returns:
            str: _description_
        """
        output = self._run_remote_command(command="squeue -u $USER")
        stdout = output.stdout
        for line in stdout.rsplit(sep="\n"):
            segments = line.split()
            if len(segments) > 1:
                if str(slurm_id) == segments[0]:
                    return segments[4]
        return "CD"
