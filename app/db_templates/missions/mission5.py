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

    head = '''<!doctype html><html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css"
        integrity="sha384-HSMxcRTRxnN+Bdg0JdbxYKrThecOKuH5zCYotlSAcp1+c8xmyTe9GYg1l9a69psu" crossorigin="anonymous">
    <link href="https://cdn.jsdelivr.net/npm/@bootcss/v3.bootcss.com@1.0.3/dist/css/bootstrap-theme.min.css"
        rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/@bootcss/v3.bootcss.com@1.0.3/examples/theme/theme.css" rel="stylesheet">
</head>

<body>
    <div class="container theme-showcase" role="main">
    <div class="col-md"><table class="table table-striped">
    <thead>
    <th>文件名称</th>
    <th>修改的时间日期</th>
    <th>未压缩文件的大小</th>
    <th>已压缩数据的大小</th>
    <th>未压缩文件的 CRC-32</th>
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
        <td>{fileinfo.filename}</td>
        <td>{fileinfo.date_time}</td>
        <td>{fileinfo.file_size.human_readable()}</td>
        <td>{fileinfo.compress_size.human_readable()}</td>
        <td>{fileinfo.CRC}</td>
        </tr>'''
    foot = '''</tbody></table></div></div></body>
<script src="https://cdn.jsdelivr.net/npm/jquery@1.12.4/dist/jquery.min.js"
    integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ"
    crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"
    integrity="sha384-aJ21OjlMXNL5UyIl/XNwTMqvzeRMZH2w8c5cRVpzpU8Y5bApTppSuUkhZXN0VxHd"
    crossorigin="anonymous"></script>
</body></html>
'''
    return head + body + foot
