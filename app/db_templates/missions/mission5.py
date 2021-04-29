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
        return '<h2>压缩包已损坏，请重新打包上传。</h2>'
    except Exception as exception:  # pylint: disable=broad-except
        return f'<h2>出现问题: {exception.args[0]}</h2>'

    output, test_ok = test_zip(file)
    if test_ok:
        output += list_zip(file)
    return output


def test_zip(obj: zipfile.ZipFile) -> (str, bool):
    """
    Test a zip file.

    Args:
        obj: a ZipFile object

    Returns:
        str: HTML output
        bool: test ok
    """
    try:
        result = obj.testzip()
    except Exception as exception:  # pylint: disable=broad-except
        return f'<h2>出现问题: {exception.args[0]}</h2>', False

    if result:
        return '<h2>压缩包已损坏，请重新打包上传。</h2>', True
    return '<h2>压缩包文件完好。</h2>', False


def list_zip(obj) -> str:
    """
    List files in a zip file.

    Args:
        obj: a ZipFile object

    Returns:
        str: HTML output
    """

    try:
        head = '''
        <table class="table table-hover align-middle"><thead><tr>
        <th scope="col">文件名称</th>
        <th scope="col">修改的时间日期</th>
        <th scope="col">未压缩文件的大小</th>
        <th scope="col">已压缩数据的大小</th>
        <th scope="col">未压缩文件的 CRC-32</th>
        </tr></thead><tbody>'''
        body = ''
        for info_obj in obj.infolist():
            fileinfo = FileInfo(filename=info_obj.filename,
                                date_time=datetime(*info_obj.date_time),
                                file_size=info_obj.file_size,
                                compress_size=info_obj.compress_size,
                                CRC=info_obj.CRC,
                                )
            body += f'''<tr>
            <td scope="row">{fileinfo.filename}</td>
            <td>{fileinfo.date_time}</td>
            <td>{fileinfo.file_size.human_readable()}</td>
            <td>{fileinfo.compress_size.human_readable()}</td>
            <td>{fileinfo.CRC}</td>
            </tr>'''
        foot = '''</tbody></table>'''
        return head + body + foot
    except Exception as exception:  # pylint: disable=broad-except
        return f'<h2>出现问题: {exception.args[0]}</h2>'
