from pymd.tools import hpc

DEFAULT_HPC = hpc.HPC(name="ada", login_node="ada", username="brara83")
DEFAULT_HPC.add_partition(partition=hpc.PartitionClass(name="q4bioq",
                                                       cpus_per_node=96,
                                                       gpus_per_node=8,
                                                       mem_per_node=1900,
                                                       nodes=1,
                                                       walltime=672,
                                                       qos="q4bio"))
DEFAULT_HPC.add_partition(partition=hpc.PartitionClass(name="defq",
                                                       cpus_per_node=96,
                                                       gpus_per_node=0,
                                                       mem_per_node=361,
                                                       nodes=63,
                                                       walltime=168))
DEFAULT_HPC.add_partition(partition=hpc.PartitionClass(name="ampere-mq",
                                                       cpus_per_node=96,
                                                       gpus_per_node=56,
                                                       mem_per_node=747,
                                                       nodes=1,
                                                       walltime=168))
DEFAULT_HPC.add_partition(partition=hpc.PartitionClass(name="ampereq",
                                                       cpus_per_node=96,
                                                       gpus_per_node=8,
                                                       mem_per_node=747,
                                                       nodes=3,
                                                       walltime=168))
DEFAULT_HPC.add_partition(partition=hpc.PartitionClass(name="compchemq",
                                                       cpus_per_node=56,
                                                       gpus_per_node=4,
                                                       mem_per_node=384,
                                                       nodes=5,
                                                       walltime=168,
                                                       qos="compchem"))

SULIS =  hpc.HPC(name="sulis", login_node="sulis", username="brara83")
SULIS.add_partition(partition=hpc.PartitionClass(name="gpu",
                                                cpus_per_node=128,
                                                gpus_per_node=3,
                                                mem_per_node=492,
                                                nodes=30,
                                                walltime=48,
                                                account="su006-101-gpu",
                                                gpu_type="ampere_a100"))
SULIS.add_partition(partition=hpc.PartitionClass(name="compute",
                                                cpus_per_node=128,
                                                gpus_per_node=0,
                                                mem_per_node=492,
                                                nodes=167,
                                                walltime=48,
                                                account="su006-101"))

ISAMBARD = hpc.HPC(name="isambardAI", login_node="u6we.aip2.isambard", username="brara83.u6we")
ISAMBARD.add_partition(partition=hpc.PartitionClass(name="workq",
                                                    cpus_per_node=288,
                                                    gpus_per_node=4,
                                                    mem_per_node=460,
                                                    nodes=1362,
                                                    walltime=24,
                                                    ))