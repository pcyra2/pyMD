import os
import pytest

from pymd.user_configs.amber_defaults import AmberConfig
from pymd.md.kernels.amber import Amber

# @pytest.mark.skip(reason="Currently dont have an environment with amber")
def test_paths():
    config = AmberConfig()

    assert os.path.isfile(str(config._CPUPath)), "CPU version of amber is not found"

def test_minimisation_toggle():
    config = AmberConfig()
    assert config._minimisation is False
    config.set_minimisation_variables(100)
    assert config._minimisation is True
    assert config.ncyc == 50
    assert config.maxcyc == 100

    config.set_minimisation_variables(200, 150)
    assert config._minimisation is True
    assert config.maxcyc == 200
    assert config.ncyc == 150


def test_dynamics_toggle():
    config = AmberConfig()
    assert config._minimisation is False
    config.set_minimisation_variables(100)
    assert config._minimisation is True
    config.set_dynamics(timestep=0.002, shake=3)
    assert config.dt == 0.002
    assert config.ntc == 3
    config.set_dynamics(timestep=0.0005, shake=1)
    assert config.dt == 0.0005
    assert config.ntc == 1
    config.set_dynamics(timestep=1)
    assert config.dt == 1
    assert config.ntc == 2


def test_temperature_controls():
    config = AmberConfig()
    config.set_heating(0, 300, 100)
    assert config.tempi == 0
    assert config.temp0 == 300
    assert config._heating_steps == 100
    config.set_heating(100, 150, 20)
    assert config.tempi == 100
    assert config.temp0 == 150
    assert config._heating_steps == 20
    config.set_temperature(120)
    assert config.tempi == 120
    assert config.temp0 == 120
    assert "ntt" in config.to_dict().keys()
    config.set_thermostat("nose_hoover")
    assert config.ntt == 9
    config.set_thermostat(2)
    assert config.ntt == 2


def test_pressure_controls():
    config = AmberConfig()
    config.set_pressure(2.1)
    assert config.pres0 == 2.1
    assert "barostat" in config.to_dict().keys()
    assert "ntp" in config.to_dict().keys()
    config.set_barostat("monte_carlo")
    assert config.barostat == 2
    config.set_barostat(1)
    assert config.barostat == 1



def test_me():
    config = AmberConfig()
    amber = Amber(config)
    amber.set_ensemble(ensemble="min", steps = 100)
    assert config._minimisation == amber.defaults._minimisation, "config should be the same as defaults."
    assert config._minimisation != amber.config._minimisation, "config should be different to kernel, class copy is broken"