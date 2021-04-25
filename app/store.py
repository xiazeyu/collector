from collections.abc import Callable
from datetime import datetime
from importlib import import_module
from typing import Any, Dict
from pathlib import Path
import json
from pydantic import BaseModel, ByteSize
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import config


class Mission(BaseModel):
    """
    The class defines a mission.
    """
    name: str
    description: str = None
    subpath: str
    ext: str
    size: ByteSize
    deadline: datetime


class Store(BaseModel):
    """
    The store for datas in a collector instance.
    """
    students: Dict[str, str] = {}
    missions: Dict[str, Mission] = {}
    checkers: Dict[str, Callable[[Path], str]] = {}
    observer: Any

    def __init__(self):
        """
        Initialize the store.

        Args:
            self: the instance

        Returns:
            (NULL)
        """
        BaseModel.__init__(self)
        self.observer = Observer()
        self.read_data()
        self.__start()

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
            #try:
            self.missions[mission.stem] = Mission(**json.loads(
                mission.read_text(encoding='UTF-8')))
            #except:  # pylint: disable=bare-except
                #pass

    def __start(self):
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
