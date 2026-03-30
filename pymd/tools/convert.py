"""Allows for easier convertion of time throughout the codebase. Can convert between time and 
steps and vice versa.
"""

from dataclasses import dataclass

@dataclass
class TimeClass:
    """Time class. Used for quick convertion of time units
    
    Attributes:
        name (str): name of the unit
        short_hand (str): short-hand name of the unit. (i.e. nanoseconds = ns)
        relative_value (float): Length of time relative to seconds. (i.e. 1 ns = 1e-9 s)
    """
    name: str
    short_hand: str
    relative_value: float
    def __init__(self, name: str, short_hand: str, relative_value: float) -> None:
        """Initialises the timeClass
    
        Args:
            name (str): name of the unit
            short_hand (str): short-hand name of the unit. (i.e. nanoseconds = ns)
            relative_value (float): Length of time relative to seconds. (i.e. 1 ns = 1e-9 s)
        """
        self.name = name
        self.short_hand = short_hand
        self.relative_value = relative_value

TIME_UNITS = [TimeClass(name="seconds", short_hand="s", relative_value=1.0),
        TimeClass(name="minutes", short_hand="min", relative_value=60.0),
        TimeClass(name="hours", short_hand="hr", relative_value=3600.0),
        TimeClass(name="days", short_hand="d", relative_value=86400.0),
        TimeClass(name="nanoseconds", short_hand="ns", relative_value=1e-9),
        TimeClass(name="picoseconds", short_hand="ps", relative_value=1e-12),
        TimeClass(name="femtoseconds", short_hand="fs", relative_value=1e-15)]

def get_time(unit:str) -> TimeClass:
    """Used as a helper function to find the timeClass object.
    
    Args:
        unit (str): Unit, either the full name, or the short-hand notation.

    Returns:
        TimeClass: the TimeClass object.
    """
    unit = unit.casefold()
    tmp = None
    for times in TIME_UNITS:
        if unit == times.name or unit == times.short_hand:
            tmp = times
    assert isinstance(tmp, TimeClass), f"Units {unit} not recognised"
    return tmp


def time(
        in_time: float = 1,
        in_unit: str = "s",
        out_unit: str = "s") -> float:
    """Converts units of time

    Args:
        in_time (float): raw value of time in the units specified
        in_unit (str): Units of raw time supplied
        out_unit (str): Units the time is desired in

    Returns:
        float: time in the specified unit
    """

    in_unit_time = get_time(unit=in_unit)
    out_unit_time =  get_time(unit=out_unit)

    return (in_time * in_unit_time.relative_value)/out_unit_time.relative_value


def steps_to_time(
        steps: int,
        time_units: str = "s",
        timestep: float = 0.002,
        timestep_units: str = "ps") -> float:
    """Converts steps to real time

    Args:
        steps (int): Number of steps 
        time_units (str): Unit of time to export as. Defaults to "s"
        timestep (float): Time between steps
        timestep_units (str): units of timestep. Defaults to "ps"
        

    Returns:
        float: total time
    """
    _time_units = get_time(unit=time_units)

    return (steps*time(in_time=timestep, in_unit=timestep_units))/_time_units.relative_value


def time_to_steps(
        sim_time: float,
        time_units: str = "ps",
        timestep: float = time(in_time=2,in_unit="fs"),
        timestep_units: str = "ps") -> int:
    """

    Args:
        sim_time (float): time to convert to steps
        time_units (str, optional): units for time to convert. Defaults to "ps".
        timestep (float, optional): time step between steps. Defaults to 2fs.
        timestep_units (str, optional): units for time step. Defaults to "ps".

    Returns:
        int: number of steps required to obtain a simulation of length 
            sim_time with the provided timestep
    """
    # timestep = time(timestep, timestep_units, "ps")
    sim_time_dt_units = time(in_time=sim_time, in_unit=time_units, out_unit=timestep_units)

    return int(sim_time_dt_units / timestep)
