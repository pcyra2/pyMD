from pyMD.MD.kernels.universal import MDJobClass
from pyMD.MD.kernels.AMBER import Amber
from pyMD.UserConfigs.AmberDefaults import AmberConfig

class MD:
    base_config: AmberConfig
    _backend: str
    kernel: Amber
    jobs = list[MDJobClass]
    current_job: MDJobClass   

    def __init__(self, backend: str = "AMBER", config: AmberConfig = AmberConfig()):
        self._backend = backend.capitalize()
        self.base_config = config

        if self._backend == "AMBER":
            self.kernel = Amber(config)
        else:
            raise NotImplementedError(f"ERROR: Backend {self._backend} not implemented yet, only AMBER is currently supported")
    

    
    def make_job(self, input_file_name: str, output_file_name: str, run_path: str ):
        self.current_job = MDJobClass(inputfile_name=input_file_name, 
                                      outputfile_name=output_file_name, 
                                      run_path=run_path)


    def commit_job(self):
        self.current_job.add_config(self.kernel.config)
