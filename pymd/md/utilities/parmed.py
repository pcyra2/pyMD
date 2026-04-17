import os
import subprocess
from pymd.tools import io

def merge_ti(structure_file: str,
        parm_file: str,
        protein_max: int,
        mutant_res_id: int,
        outfile: str,
        parmed_file: str = "parmed.in",
        path: str = "./"):
    file = f"""loadRestrt {structure_file}
setOverwrite True
tiMerge :1-{protein_max} :{protein_max+1}-{2*protein_max} :{mutant_res_id} :{mutant_res_id+protein_max}
outparm {outfile}.parm7 {outfile}.rst7
quit
"""
    print(f"INFO: Running parmed -p {parm_file} -i {parmed_file} > {parmed_file.replace('.in','.log')} in {path}")
    io.text_dump(file, os.path.join(path, parmed_file))
    with open(os.path.join(path, parmed_file.replace(".in",".log")), "w") as f:
        subprocess.run(["parmed", "-p", parm_file, "-i", parmed_file],
                    cwd=path, stdout=f, check=True)
    