from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from importlib import import_module, invalidate_caches
from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging

from async_property import AwaitLoader, async_cached_property
from pydantic import BaseModel, ByteSize
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_CREATED
from watchdog.observers import Observer

import config

logger = logging.getLogger(__name__)

class StatusEnum(str, Enum):
    """
    The class defines the enum of submission status.
    """
    LOCKED = '已锁定'
    UPLOADED = '已提交'
    EMPTY = '未提交'


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


class UserFileInfo(AwaitLoader):
    """
    The class defines info of user file.
    """
    student: Student
    mission: Mission
    status: StatusEnum = StatusEnum.EMPTY
    sub_file_path: Optional[Path] = None
    sub_size: Optional[ByteSize] = None
    sub_time: Optional[datetime] = None

    def __init__(self, mission: Mission, student: Student):
        """
        Initialize the UserFileInfo.

        Args:
            self: the instance

        Returns:
            UserFileInfo
        """
        self.mission = mission
        self.student = student
        AwaitLoader.__init__(self)

    async def load(self) -> None:
        """
        load the file info of a student.
        Called by AwaitLoader before loading properties.

        Args:
            self: the instance

        Returns:
            None
        """
        mis = self.mission
        stu = self.student
        mission_path = config.received_path / mis.subpath
        mission_path.mkdir(parents=True, exist_ok=True)
        unconfirmed_filepath = mission_path / \
            f'{stu.stu_id}-{stu.name}.unconfirmed.{mis.ext}'
        confirmed_filepath = mission_path / \
            f'{stu.stu_id}-{stu.name}.{mis.ext}'

        if confirmed_filepath.exists():
            self.status = StatusEnum.LOCKED
            self.sub_file_path = confirmed_filepath
            self.sub_size = ByteSize(confirmed_filepath.stat().st_size)
            self.sub_time = datetime.fromtimestamp(
                confirmed_filepath.stat().st_mtime)
        if unconfirmed_filepath.exists():
            self.status = StatusEnum.UPLOADED
            self.sub_file_path = unconfirmed_filepath
            self.sub_size = ByteSize(unconfirmed_filepath.stat().st_size)
            self.sub_time = datetime.fromtimestamp(
                unconfirmed_filepath.stat().st_mtime)

    @async_cached_property
    async def submitted(self) -> bool:
        """
        (Read-only)
        If student has submitted.

        Args:
            self: the instance

        Returns:
            Bool
        """
        if self.status in [StatusEnum.LOCKED, StatusEnum.UPLOADED]:
            return True
        return False


class MissionStatus(AwaitLoader):
    """
    The class defines a mission status.
    """
    mission: Mission
    student: Student
    finish_rate: Optional[float]

    def __init__(self, mission: Mission,
                 student: Student):
        """
        Initialize the MissionStatus.

        Args:
            self: the instance

        Returns:
            MissionStatus
        """
        self.mission = mission
        self.student = student
        self.finish_rate = None

        AwaitLoader.__init__(self)

    async def get_finish_rate(self, stu_count:int) -> Optional[float]:
        """
        Calculate the finish rate of a mission.

        Args:
            self: the instance
            stu_count: count of students

        Returns:
            Optional[Float]
        """

        mission_path = config.received_path / self.mission.subpath
        mission_path.mkdir(parents=True, exist_ok=True)
        self.finish_rate = 100 * len(list(mission_path.glob('*'))) / stu_count

    @async_cached_property
    async def file_info(self) -> UserFileInfo:
        """
        (Read-only)
        Get the user file info from a student.

        Args:
            self: the instance

        Returns:
            UserFileInfo
        """
        return await UserFileInfo(student=self.student,
                                  mission=self.mission)

    @property
    def remain(self) -> timedelta:
        """
        (Read-only)
        Remaining timedelta.

        Args:
            self: the instance

        Returns:
            Timedelta
        """
        return self.mission.deadline - datetime.today()

    @async_cached_property
    async def avaliable(self) -> bool:
        """
        (Read-only)
        If submission is avaliable to student.

        Args:
            self: the instance

        Returns:
            Bool
        """
        if (await self.file_info).status == StatusEnum.LOCKED or self.remain.total_seconds() < 0:
            return False
        return True


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

    def read_data(self) -> None:
        """
        Read data from local storage.

        Args:
            self: the instance

        Returns:
            None
        """
        logger.info("READ_DATA")
        self.read_students()
        self.read_missions()
        self.read_checkers()

    def read_students(self) -> None:
        """
        Read students data from local storage.

        Args:
            self: the instance

        Returns:
            None
        """
        logger.info("READ_STU_DATA")
        self.students = {}
        if config.students_path.exists():
            try:
                self.students = json.loads(
                    config.students_path.read_text(encoding='UTF-8'))
            except Exception as exception:  # pylint: disable=broad-except
                logger.warning('config invalid: %s', exception.args[0])

    def read_missions(self) -> None:
        """
        Read missions data from local storage.

        Args:
            self: the instance

        Returns:
            None
        """
        logger.info("READ_MIS_DATA")
        self.missions = {}
        for mission in list(config.missions_path.glob('**/*.json')):
            try:
                self.missions[mission.stem] = Mission(
                    mission_url=mission.stem,
                    **json.loads(mission.read_text(encoding='UTF-8')))
            except Exception as exception:  # pylint: disable=broad-except
                logger.warning('config invalid: %s', exception.args[0])

    def read_checkers(self) -> None:
        """
        Read chckers data from local storage.

        Args:
            self: the instance

        Returns:
            None
        """
        logger.info("READ_CHK_DATA")
        self.checkers = {}
        for checker in list(config.missions_path.glob('**/*.py')):
            try:
                invalidate_caches()
                self.checkers[checker.stem] = import_module(
                    f'{config.import_root}{checker.stem}').main
            except Exception as exception:  # pylint: disable=broad-except
                logger.warning('config invalid: %s', exception.args[0])

    def __start_observer(self) -> None:
        """
        Start observation of students, missions and checkers.

        Args:
            self: the instance

        Returns:
            None
        """

        event_handler = FileSystemEventHandler()

        def dispatch(event) -> None:
            """
            Dispatches events to the appropriate methods.

            Args:
                event: The event object representing the file system event.

            Returns:
                None
            """
            if event.is_directory:
                return

            if event.event_type == EVENT_TYPE_CREATED:
                return

            path = Path(event.src_path)
            logger.debug('%s:%s', event.event_type, event.src_path)
            if path.name == config.STUDENTS_SUBPATH:
                self.read_students()
            elif path.suffix == '.json':
                self.read_missions()
            elif path.suffix == '.py':
                self.read_checkers()

        event_handler.dispatch = dispatch

        self.observer.schedule(
            event_handler, config.db_path, recursive=True)
        self.observer.start()
