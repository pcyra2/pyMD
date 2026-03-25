from pymd.tools import hpc

DEFAULT_HPC = hpc.HPC(name="ada", login_node="hpclogin02.ada.nottingham.ac.uk", username="brara83")
DEFAULT_HPC.add_partition(hpc.PartitionClass("q4bioq", 96, 8, 1900, 1, 672, "q4bio" ))
DEFAULT_HPC.add_partition(hpc.PartitionClass("defq", 96, 0, 361, 63, 168))
DEFAULT_HPC.add_partition(hpc.PartitionClass("ampere-mq", 96, 56, 747, 1, 168))
DEFAULT_HPC.add_partition(hpc.PartitionClass("ampereq", 96, 8, 747, 3, 168))
DEFAULT_HPC.add_partition(hpc.PartitionClass("compchemq", 56, 4, 384, 5, 168, "compchem"))
