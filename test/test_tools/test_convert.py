import pymd.tools.convert as convert
import numpy
import pytest

def test_time_converter():
    seconds = 120
    minutes = 2
    hours = 2/60
    assert convert.time(seconds, "seconds", "minutes" ) == minutes
    assert convert.time(minutes, "min", "hr") == hours
    assert convert.time(hours, "hr", "s") == seconds
    with pytest.raises(AssertionError): # This should raise an Assertation error
        convert.get_time("angstrom") 

def test_step_converter():
    steps = 5000 # 5000 steps should be 10 ps in 2 fs time steps
    timestep = 0.002 # in ps. therefore 2 fs
    time = 10 # ps

    assert convert.time(2, "fs", "ps") == timestep
    assert numpy.isclose(convert.steps_to_time(steps, "ps", timestep), time)
    assert convert.time_to_steps(time, "ps", timestep, "picoseconds") == steps
    assert convert.time_to_steps(time, "ns", timestep, "ps") == steps*1e3
    assert convert.time_to_steps(10, "fs", 2, "fs") == 5 # 10 fs in 2fs timesteps 