from pathlib import Path

DEBUG_FLAG: bool = False


ROOT_PATH: Path = Path.cwd()
DP_SUBPATH: str = 'db'
RECEIVED_SUBPATH: str = 'received'
STUDENTS_SUBPATH: str = 'students.json'
MISSION_SUBPATH: str = 'missions'

DATETIME_FORMAT = '%a %Y-%m-%d %H:%M:%S'

# Below are auto-computed
# You should not change

db_path: Path = ROOT_PATH / DP_SUBPATH
received_path: Path = ROOT_PATH / RECEIVED_SUBPATH
students_path: Path = db_path / STUDENTS_SUBPATH
missions_path: Path = db_path / MISSION_SUBPATH

import_root: str = f'{DP_SUBPATH}.{MISSION_SUBPATH}.'
