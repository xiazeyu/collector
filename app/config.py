from pathlib import Path
import logging
import os

ROOT_PATH: Path = Path.cwd()
DP_SUBPATH: str = 'db'
RECEIVED_SUBPATH: str = 'received'
STUDENTS_SUBPATH: str = 'students.json'
MISSION_SUBPATH: str = 'missions'

DATETIME_FORMAT: str = '%a %Y-%m-%d %H:%M:%S'

# Below are auto-computed
# You should not change

LOG_LEVEL = logging.DEBUG
if os.getenv('PRODUCTION') == 1:
    LOG_LEVEL = logging.WARNING

logging.basicConfig(level=LOG_LEVEL)

db_path: Path = ROOT_PATH / DP_SUBPATH
received_path: Path = ROOT_PATH / RECEIVED_SUBPATH
students_path: Path = db_path / STUDENTS_SUBPATH
missions_path: Path = db_path / MISSION_SUBPATH

import_root: str = f'{DP_SUBPATH}.{MISSION_SUBPATH}.'


def get_file_name(stu, ext: str, confirmed: bool = True) -> str:
    """
    Get the filename.

    Args:
        stu: student object
        ext: file ext name
        confirmed: if is confirmed file

    Returns:
        str: the file name
    """
    if confirmed:
        return f'{stu.stu_id}-{stu.name}.{ext}'
    else:
        return f'{stu.stu_id}-{stu.name}.unconfirmed.{ext}'
