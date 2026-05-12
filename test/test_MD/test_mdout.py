import os
from pymd.md.kernels.amber import Amber

TEST_PATH = "./test/test_MD/example_files"

def test_mdout():
    md = Amber(start_coordinates="input.pdb", parm_file="parm7.top")
    md.set_npt(steps=500000,
               temperature=300,
               pressure = 1)
    md.set_outputs(energy=10, restart=100, trajectory=int(500000/200))
    md.build(input_file_name="NPT1",
            input_structure="NVT1.ncrst",
            output_file_name="NPT1",
            run_path=TEST_PATH,
            gpu=True)
    
    data = md.parse_outfile(file=os.path.join(TEST_PATH, f"{md.jobs[-1].outputfile_name}.out"), variables=["Etot", "TEMP(K)", "VOLUME", "PRESS"])
#     print(data)
#     assert False