from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from importlib import import_module, invalidate_caches
import logging
from pathlib import Path
from typing import Any, Dict, Optional, ForwardRef
import json
from pydantic import BaseModel, ByteSize
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_CREATED
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


class MissionStatus(BaseModel):  # pylint: disable=too-many-instance-attributes
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
    checkers: Dict[str, Callable]
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
        self.__start_observer()

    def read_data(self):
        """
        Read data from local storage.

        Args:
            self: the instance

        Returns:
            (NULL)
        """
        logging.debug("READ_DATA")
        self.read_students()
        self.read_missions()
        self.read_checkers()

    def read_students(self):
        """
        Read students data from local storage.

        Args:
            self: the instance

        Returns:
            (NULL)
        """
        logging.debug("READ_STU_DATA")
        self.students = {}
        if config.students_path.exists():
            try:
                self.students = json.loads(
                    config.students_path.read_text(encoding='UTF-8'))
            except:  # pylint: disable=bare-except
                pass

    def read_missions(self):
        """
        Read missions data from local storage.

        Args:
            self: the instance

        Returns:
            (NULL)
        """
        logging.debug("READ_MIS_DATA")
        self.missions = {}
        for mission in list(config.missions_path.glob('**/*.json')):
            try:
                self.missions[mission.stem] = Mission(
                    mission_url=mission.stem,
                    **json.loads(mission.read_text(encoding='UTF-8')))
            except:  # pylint: disable=bare-except
                pass

    def read_checkers(self):
        """
        Read chckers data from local storage.

        Args:
            self: the instance

        Returns:
            (NULL)
        """
        logging.debug("READ_CHK_DATA")
        self.checkers = {}
        for checker in list(config.missions_path.glob('**/*.py')):
            try:
                invalidate_caches()
                self.checkers[checker.stem] = import_module(
                    f'{config.import_root}{checker.stem}').main
            except:  # pylint: disable=bare-except
                pass

    def __start_observer(self):
        """
        Start observation of students, missions and checkers.

        Args:
            self: the instance

        Returns:
            (NULL)
        """

        event_handler = FileSystemEventHandler()
        def dispatch(event):
            """Dispatches events to the appropriate methods.

            :param event:
                The event object representing the file system event.
            :type event:
                :class:`FileSystemEvent`
            """
            if event.is_directory:
                return

            if event.event_type == EVENT_TYPE_CREATED:
                return

            path = Path(event.src_path)
            logging.debug('%s:%s', event.event_type, event.src_path)
            if(path.name == config.STUDENTS_SUBPATH):
                self.read_students()
            elif(path.suffix == '.json'):
                self.read_missions()
            elif(path.suffix == '.py'):
                self.read_checkers()

        event_handler.dispatch = dispatch

        self.observer.schedule(
            event_handler, config.db_path, recursive=True)
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
    unconfirmed_filepath = mission_path / \
        f'{stu.stu_id}-{stu.name}.unconfirmed.{mission.ext}'
    confirmed_filepath = mission_path / \
        f'{stu.stu_id}-{stu.name}.{mission.ext}'
    if confirmed_filepath.exists():
        return (StatusEnum.LOCKED,
                confirmed_filepath,
                ByteSize(confirmed_filepath.stat().st_size),
                datetime.fromtimestamp(confirmed_filepath.stat().st_mtime))
    if unconfirmed_filepath.exists():
        return (StatusEnum.UPLOADED,
                unconfirmed_filepath,
                ByteSize(unconfirmed_filepath.stat().st_size),
                datetime.fromtimestamp(unconfirmed_filepath.stat().st_mtime))
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
