import zipfile
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, ByteSize


class FileInfo(BaseModel):
    """
    This class defines infos of a file
    """
    filename: str
    date_time: datetime
    file_size: ByteSize
    compress_size: ByteSize
    CRC: int


def main(file_path: Path) -> str:
    """
    Verify, list files in a zip file.

    Args:
        file_path: file path

    Returns:
        str: HTML output
    """
    try:
        file = zipfile.ZipFile(file_path)
    except zipfile.BadZipFile:
        return '压缩包已损坏，请重新打包上传。<br>'
    output = test_zip(file)
    output += list_zip(file)
    return output


def test_zip(obj: zipfile.ZipFile):
    """
    Test a zip file.

    Args:
        obj: a ZipFile object

    Returns:
        str: HTML output
    """
    result = obj.testzip()
    if result:
        return '压缩包已损坏，请重新打包上传。<br>'
    return '压缩包文件完好。<br>'


def list_zip(obj):
    """
    List files in a zip file.

    Args:
        obj: a ZipFile object

    Returns:
        str: HTML output
    """

    head = '''<table border="1"><tr>
    <th>文件名称</th>
    <th>修改的时间日期</th>
    <th>未压缩文件的大小</th>
    <th>已压缩数据的大小</th>
    <th>未压缩文件的 CRC-32</th>
    </tr>'''

    body = ''
    for info_obj in obj.infolist():
        fileinfo = FileInfo(filename=info_obj.filename,
                            date_time=datetime(*info_obj.date_time),
                            file_size=info_obj.file_size,
                            compress_size=info_obj.compress_size,
                            CRC=info_obj.CRC,
        )
        body += f'''<tr>
        <td>{fileinfo.filename}</td>
        <td>{fileinfo.date_time}</td>
        <td>{fileinfo.file_size.human_readable()}</td>
        <td>{fileinfo.compress_size.human_readable()}</td>
        <td>{fileinfo.CRC}</td>
        </tr>'''

    foot = '</table>'
    return head + body + foot
