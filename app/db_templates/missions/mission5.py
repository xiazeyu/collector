# zip file, list dir, verify

import zipfile

def check(filePath):
    file = zipfile.ZipFile(filePath)
    output = ''

    output += testZip(file)
    output += listZip(file)
    return output

def testZip(obj):
    result = obj.testzip()
    if result is None:
        return '压缩包文件完好。<br>'
    else:
        return '压缩包已损坏，请重新打包上传。<br>'

def listZip(obj):
    nameList = obj.namelist()
    head = '<table border="1"><tr><th>文件名称</th><th>修改的时间日期</th><th>未压缩文件的大小</th><th>已压缩数据的大小</th><th>未压缩文件的 CRC-32</th></tr>'
    body = ''
    for f in nameList:
        i = obj.getinfo(f)
        print(i)
        body += f'<tr><td>{i.filename}</td><td>{i.date_time}</td><td>{i.file_size}</td><td>{i.compress_size}</td><td>{i.CRC}</td></tr>'
    foot = '</table>'
    return head + body + foot
