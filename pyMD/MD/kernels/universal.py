from pyMD.UserConfigs.AmberDefaults import AmberConfig

import os

class JobClass:
    inputfile: list[str]
    inputfile_name: str
    outputfile_name: str
    runline: str|list[str]
    run_path: str
    complete: bool = False
    config: AmberConfig

    def __init__(self, 
                inputfile_name: str,
                outputfile_name:str,
                run_path: str = "./"
                ):
        self.inputfile_name = inputfile_name
        self.outputfile_name = outputfile_name
        self.complete = False

    def add_inputfile(self, inputfile: list[str]):
        self.inputfile = inputfile

    def add_config(self, config: AmberConfig):
        self.config = config

    def kernel(self):
        if os.path.isfile(os.path.join(self.run_path, self.inputfile_name)) is False:
            with open(os.path.join(self.run_path, self.inputfile_name), "w") as f:
                f.writelines(self.inputfile)
            
