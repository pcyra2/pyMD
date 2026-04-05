import dataclasses

from pymd.tools import io

@dataclasses.dataclass(repr=True, )
class StageData:
    def add_steps(self, steps: list[str]) -> None:
        for step in steps:
            setattr(self, step, "Not Started")


    def update_step(self, step: str, status: str) -> None:
        setattr(self, step, status)

    def __str__(self) -> str:
        lines = ""
        for key, val in vars(self).items():
            lines += f"{key} = {val}\n"
        return lines
    
    def _to_dict(self) -> dict:
        return {key:value for key, value in vars(self).items() if not key.startswith('_')}

    def get_status(self, step: str) -> str:
        return getattr(self, step)

class StatusTracker:
    _file_path: str

    def __init__(self, stages: list[str] = [], file_path: str = "STATUS.json") -> None:
        self._file_path = file_path
        for stage in stages:
            setattr(self, stage, StageData())
    
    def add_stage(self, stage: str, steps: list[str]|None):
        if steps is None:
            setattr(self, stage, StageData())
        else:
            stage_data = StageData()
            stage_data.add_steps(steps)
            setattr(self, stage, stage_data)
        io.json_dump(data=self._to_dict(), path=self._file_path)

    def add_steps(self, stage: str, steps: list[str]) -> None:
        stage_data: StageData = getattr(self, stage)
        stage_data.add_steps(steps=steps)
        setattr(self, stage, stage_data)
        io.json_dump(data=self._to_dict(), path=self._file_path)

    def _to_dict(self):
        return {key:value._to_dict() for key, value in vars(self).items() if not key.startswith('_')}
    
    def update_step(self, stage: str, step: str, status: str) -> None:
        stage_data: StageData = getattr(self, stage)
        stage_data.update_step(step=step, status=status)
        setattr(self, stage, stage_data)
        io.json_dump(data=self._to_dict(), path=self._file_path)

    def from_dict(self) -> None:
        data = io.json_read(path=self._file_path)
        for stage, stage_data in data.items():
            sd = StageData()
            for step, status in stage_data.items():
                sd.update_step(step=step, status=status)
            setattr(self, stage, sd)

    def get_status(self, stage: str, step: str) -> str:
        stg: StageData =  getattr(self, stage)
        return stg.get_status(step=step)
