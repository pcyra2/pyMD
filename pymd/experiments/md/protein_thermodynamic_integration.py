"""
This script should automatically run thermodynamic integration.
"""


from pymd.md.kernels.amber import Amber
from pymd.md.recipies import thermodynamic_integration as TI
from pymd.md.recipies import standard_md, custom_recipies
from pymd.md.utilities import cpptraj, leap
from pymd.tools import io, pdb
from pymd.tools.status_tracker import StatusTracker

# @dataclass
class ConfigClass:
    """
    Contains all the information needed to run the TI calculation.

    Attributes:
        input_file (str): File containing this class.
        input_data_dir (str): Directory where all other immutable data is contained such as input 
            protein and parameter files.
        run_dir (str): Directory to run the calculation.
        base_protein (str): File containing the wildtype protein pdb file
        base_ligand (str): File containing the wildtype ligand mol2 file. There should also be a 
            frcmod file with the same prefix in this directory. 
        mutation (str): Amino acid to mutate to.
        mutation_resid (int): Resid of residue you want to mutate.
        cpus (int): Number of cores to give a single calculation
        gpus (int) Number of GPU's to give a single calculation

    """
    input_file: str = "Job.conf"
    status_file: str = "./status.json"
    input_data_dir: str = "./input_data"
    run_dir: str = "./"
    protein_pdb: str = "Protein.pdb"
    ligand_mol2: str = "Ligand.mol2"
    mutation: str = ""
    mutation_resid: int = 0
    forcefield: str = "ff19SB"
    box: int = 10
    cpus: int = 12
    gpus: int = 1
    hpc: dict = dict(partition = "compchemq",
                    module_files = ["amber-uon/gcc11.3.0/24", "cuda-12.2.2"],
                    wall_time = 168)

    def __init__(self) -> None:
        self.input_file = self.input_file
        self.input_data_dir = self.input_data_dir
        self.run_dir = self.run_dir
        self.protein_pdb = self.protein_pdb
        self.ligand_mol2 = self.ligand_mol2
        self.mutation = self.mutation
        self.mutation_resid = self.mutation_resid
        self.forcefield = self.forcefield
        self.box = self.box
        self.cpus = self.cpus
        self.gpus = self.gpus
        self.hpc = self.hpc

    def to_dict(self)->dict:
        """Returns a dictionary of the class attributes"""
        return {key:value for key, value in vars(self).items()}

    def from_dict(self, d: dict) -> None:
        """
        Initialises config from dictionary.

        Args:
            d (dict): dictionary containing input variables. 
        """
        for key, value in d.items():
            if key in vars(self).keys():
                setattr(self, key, value)


def main() -> None:
    """
    Runs TI.
    """
    config = ConfigClass()
    if os.path.isfile(path=config.input_file):
        c_data = io.json_read(path=config.input_file)
        config.from_dict(d=c_data)
    # io.json_dump(data=config.to_dict(), path=config.input_file)

    assert os.path.isdir(config.input_data_dir)
    STATUS = StatusTracker(file_path =  config.status_file)
    if os.path.isfile(path=config.status_file):
        print(f"INFO: Reading job status from {config.status_file}")
        STATUS.from_dict()

    if hasattr(STATUS, "setup") is False:
        STATUS.add_stage(stage="setup", steps=["data manipulation",
                                    "leap", 
                                    "min1", 
                                    "min2",
                                    "heat", 
                                    "nvt",
                                    "npt1",
                                    "npt2",
                                    "npt3"])


    ## Setup the system
    setup_path = os.path.join(config.run_dir, "setup")
    io.make_dir(path=setup_path)

    shutil.copy(os.path.join(config.input_data_dir, config.protein_pdb), 
                os.path.join(setup_path, config.protein_pdb))
    shutil.copy(os.path.join(config.input_data_dir, config.ligand_mol2), 
                os.path.join(setup_path, config.ligand_mol2))
    shutil.copy(os.path.join(config.input_data_dir, config.ligand_mol2.replace("mol2", "frcmod")), 
                os.path.join(setup_path, config.ligand_mol2.replace("mol2", "frcmod")))
    
    STATUS.update_step(stage="setup", step="data manipulation", status="complete")

    if STATUS.setup.leap != "complete":
        print("INFO: Running initial leap step")
        leap_in = leap.gen_leap(ligand_name=config.ligand_mol2.replace(".mol2",""), pdb_file=config.protein_pdb, forcefield=config.forcefield, water="TIP3P")

        io.text_dump(text=leap_in, path=os.path.join(setup_path, "leap.in"))
        leap.run_leap(path=setup_path)
        STATUS.update_step("setup", "leap", "run")
        tmp = leap.check_leap_log(path=setup_path)
        if tmp is True:
            STATUS.update_step("setup", "leap", "complete")
        else: 
            STATUS.update_step("setup", "leap", "error")
    
    protein_max_resid: int = pdb.get_protein_res_id_range(lines=io.text_read(path=os.path.join(setup_path, config.protein_pdb)))
    
    md = Amber(start_coordinates="complex.rst7",
               parm_file="complex.parm7")
    md.describe_structure(protein_residue_start=1,
                protein_residue_end=protein_max_resid,
                )#TODO Add ligand and cofactor defenition.
    md.define_hardware(cpu = config.cpus, gpu = config.gpus)
    # if STATUS.setup.minimize1 != "complete":
    #     md.minimize(input_structure="complex.rst7", 
    #                 job_name="min1",
    #                 steps=10000,
    #                 restraints=f"':1-{protein_max_resid}'",
    #                 run_path=setup_path,
    #                 steps_steepest=5000,
    #                 traj_out=0, 
    #                 restart_out=500,
    #                 energy_out=10
    #                 )
    #     md.jobs[-1].exe(gpu=True)
    #     STATUS.update_step(stage="setup", step="minimize1", status="complete")

    # if STATUS.setup.minimize2 != "complete":
    #     md.minimize(input_structure="min1.rst7", 
    #                 job_name="min2",
    #                 steps=10000,
    #                 restraints=None,
    #                 run_path=setup_path,
    #                 steps_steepest=5000,
    #                 traj_out=0, 
    #                 restart_out=500,
    #                 energy_out=10
    #                 )
    #     md.jobs[-1].exe(gpu=True)
    #     STATUS.update_step(stage="setup", step="minimize2", status="complete")

    md = custom_recipies.qian_init_system(mm=md, path=setup_path)
    for job in md.jobs:
        if STATUS.get_status("setup", job.inputfile_name) != "complete":
            job.exe(gpu=True)
            STATUS.update_step("setup", job.inputfile_name, "complete")


if __name__ == "__main__":
    main()
