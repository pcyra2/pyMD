from pyMD.UserConfigs.AmberDefaults import AmberConfig

import os

def test_paths():
    config = AmberConfig()
    assert os.path.isfile(config.CPUPath), "CPU version of amber is not found"
    assert os.path.isfile(config.GPUPath), "GPU version of amber is not found"

def test_minimisation_toggle():
    config = AmberConfig()
    assert config._minimisation == False
    config.set_minimisation(100)
    assert config._minimisation == True
    assert config.ncyc == 50
    assert config.maxcyc == 100

    config.set_minimisation(200, 150)
    assert config._minimisation == True
    assert config.maxcyc == 200
    assert config.ncyc == 150


def test_dynamics_toggle():
    config = AmberConfig()
    assert config._minimisation == False
    config.set_minimisation(100)
    assert config._minimisation == True
    config.set_dynamics(timestep=0.002, shake=3)
    assert config.dt == 0.002
    assert config.nct == 3
    config.set_dynamics(timestep=0.0005, shake=1)
    assert config.dt == 0.0005
    assert config.nct == 1
    config.set_dynamics(timestep=1)
    assert config.dt == 1
    assert config.nct == 2


def test_me():
    config = AmberConfig()
    print(config.to_dict())
    config.barostat = 1
    print(config.to_dict)
    assert False