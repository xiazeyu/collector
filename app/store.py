from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Optional, ForwardRef
import json
from pydantic import BaseModel, ByteSize
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import config


class Student(BaseModel):
    """
    The class defines a student.
    """
    stu_id: str
    name: str


class Mission(BaseModel):
    """
    The class defines a mission.
    """
    name: str
    description: Optional[str] = None
    mission_url: str
    deadline: datetime
    ext: str = 'zip'
    size: ByteSize = '16M'
    subpath: str


class StatusEnum(str, Enum):
    """
    The class defines the enum of submission status.
    """
    LOCKED = '已锁定'
    UPLOADED = '已提交'
    EMPTY = '未提交'


MissionStatus = ForwardRef('MissionStatus')

class MissionStatus(BaseModel):
    """
    The class defines a mission status.
    """
    mission: Mission
    student: Student
    stu_count: int
    finish_rate: float = 0
    remain: timedelta = 0
    status: StatusEnum = StatusEnum.EMPTY
    sub_file_path: Optional[Path]
    sub_size: Optional[ByteSize]
    sub_time: Optional[datetime]
    avaliable: bool = False
    submitted: bool = False

    async def fetch(self) -> MissionStatus:
        """
        Fetch the real mission status.

        Args:
            self: the instance

        Returns:
            Coroutine: MissionStatus Coroutine
        """
        (self.status,
         self.sub_file_path,
         self.sub_size,
         self.sub_time) = await file_status(self.student,
                                            self.mission)
        self.finish_rate = await mission_finish_rate(self.mission, self.stu_count)
        self.remain = self.mission.deadline - datetime.today()
        self.avaliable = True
        self.submitted = False
        if self.status == StatusEnum.LOCKED or self.remain.total_seconds() < 0:
            self.avaliable = False
        if self.status == StatusEnum.LOCKED or self.status == StatusEnum.UPLOADED:
            self.submitted = True
        return self


MissionStatus.update_forward_refs()

class Store(BaseModel):
    """
    The store for datas in a collector instance.
    """
    students: Dict[str, str]
    missions: Dict[str, Mission]
    checkers: Dict[str, Callable[[Path], str]]
    observer: Any

    def __init__(self):
        """
        Initialize the store.

        Args:
            self: the instance

        Returns:
            Store Instance
        """
        BaseModel.__init__(self,
                           students={},
                           missions={},
                           checkers={},
                           observer=Observer())
        self.read_data()
        self.__start_observe()

    def read_data(self):
        """
        Read data from local storage.

        Args:
            self: the instance

        Returns:
            (NULL)
        """
        if config.DEBUG_FLAG:
            print("READ_DATA")
        self.students = {}
        self.missions = {}
        self.checkers = {}
        if config.students_path.exists():
            try:
                self.students = json.loads(
                    config.students_path.read_text(encoding='UTF-8'))
            except:  # pylint: disable=bare-except
                pass
        for checker in list(config.missions_path.glob('**/*.py')):
            try:
                self.checkers[checker.stem] = import_module(
                    f'{config.import_root}{checker.stem}').main
            except:  # pylint: disable=bare-except
                pass
        for mission in list(config.missions_path.glob('**/*.json')):
            try:
                self.missions[mission.stem] = Mission(
                    mission_url=mission.stem,
                    **json.loads(mission.read_text(encoding='UTF-8')))
            except:  # pylint: disable=bare-except
                pass

    def __start_observe(self):
        """
        Start observation of students, missions and checkers.

        Args:
            self: the instance

        Returns:
            (NULL)
        """

        event_handler = FileSystemEventHandler()
        event_handler.on_any_event = lambda _: self.read_data()
        self.observer.schedule(
            event_handler, config.db_path.as_posix(), recursive=True)
        self.observer.start()


async def file_status(stu: Student,
                      mission: Mission) -> (StatusEnum,
                                            Optional[Path],
                                            Optional[ByteSize],
                                            Optional[datetime]):
    """
    Generate the file status of a student.

    Args:
        stu: student
        mission: mission body

    Returns:
        (StatusEnum, Path, ByteSize, datetime)
    """
    mission_path = config.received_path / mission.subpath
    mission_path.mkdir(parents=True, exist_ok=True)
    unconfirmed_filepath = f'{stu.stu_id}-{stu.name}.unconfirmed.{mission.ext}'
    confirmed_filepath = f'{stu.stu_id}-{stu.name}.{mission.ext}'
    if (mission_path / confirmed_filepath).exists():
        return (StatusEnum.LOCKED,
                mission_path / confirmed_filepath,
                (mission_path / confirmed_filepath).stat().st_size,
                datetime.fromtimestamp((mission_path /
                                        confirmed_filepath).stat().st_mtime))
    elif (mission_path / unconfirmed_filepath).exists():
        return (StatusEnum.UPLOADED,
                mission_path / unconfirmed_filepath,
                (mission_path / unconfirmed_filepath).stat().st_size,
                datetime.fromtimestamp((mission_path /
                                       unconfirmed_filepath).stat().st_mtime))
    else:
        return (StatusEnum.EMPTY,
                None,
                None,
                None)


async def mission_finish_rate(mission: Mission, stu_count: int) -> float:
    """
    Calculate the finish rate of a mission.

    Args:
        mission: mission body

    Returns:
        Float
    """
    mission_path = config.received_path / mission.subpath
    mission_path.mkdir(parents=True, exist_ok=True)
    return 100 * len(list(mission_path.glob('*'))) / stu_count
