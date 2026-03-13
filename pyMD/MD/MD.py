from pyMD.MD.kernels.universal import JobClass
from pyMD.MD.kernels.AMBER import Amber
from pyMD.UserConfigs.AmberDefaults import AmberConfig

class MD:
    base_config: AmberConfig
    _backend: str
    kernel: Amber
    jobs = list[JobClass]
    current_job: JobClass   

    def __init__(self, backend: str = "AMBER", config: AmberConfig = AmberConfig()):
        self._backend = backend.capitalize()
        self.base_config = config

        if self._backend == "AMBER":
            self.kernel = Amber(config)
        else:
            raise NotImplementedError(f"ERROR: Backend {self._backend} not implemented yet, only AMBER is currently supported")
    

    
    def make_job(self, ):
        self.current_job = JobClass()
        pass

    def commit_job(self):
        pass
