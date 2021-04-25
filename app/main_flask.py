
from flask import Flask, render_template, make_response, request, redirect, url_for

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


TIME_FORMAT = '%a %Y-%m-%d %H:%M:%S'


@app.route('/')
@app.route('/login')
def login(info=None):
    stuNum = request.args.get("stuNum") or request.cookies.get("stun")
    info = request.args.get("info")
    # print(stuNum, request.cookies.get("stun"), request.args.get("stuNum"))
    if info == None:
        info = ""
    if stuNum == None:
        resp = make_response(render_template('login.html', info=info))
    elif stuNum not in students:
        resp = make_response(render_template(
            'login.html', info="您的学号有误。请核对后再试。"))
    else:
        resp = make_response(redirect(url_for('missions')))
        resp.set_cookie("stun", stuNum, max_age=2592000)
    return resp


@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login', info="已登出。")))
    resp.delete_cookie("stun")
    return resp


@app.route('/missions')
def missions():
    # print(missions)
    stuNum = request.cookies.get("stun")
    if stuNum not in students:
        resp = make_response(redirect(url_for('login', info="请先登录。")))
    else:
        missonStatus = []
        for key in sorted(missionsDb.keys()):
            missonStatus.append(genMissonStatus(stuNum, key, missionsDb[key]))
        # print(missonStatus)
        resp = make_response(render_template(
            'missions.html', student_name=students[stuNum], missions=missonStatus, progress='%.2f' % genProgress(missonStatus), nowDateTime=datetime.today().strftime(timeFormat)))
    return resp


@app.route('/submit/<missionurl>', methods=['GET', 'POST'])
def submit(missionurl, info=None):
    stuNum = request.cookies.get("stun")
    missionObj = missionsDb[missionurl]
    missionStatus = genMissonStatus(stuNum, missionurl, missionObj)
    info = request.args.get("info")
    if info == None:
        info = ""
    if stuNum not in students:
        resp = make_response(redirect(url_for('login', info="请先登录。")))
    else:
        if request.method == 'POST':
            if 'file' not in request.files:
                return make_response(redirect(url_for('submit', missionurl=missionurl, info="No file part")))
            f = request.files['file']
            if f.filename == '':
                return make_response(redirect(url_for('submit', missionurl=missionurl, info="未选择提交文件呢。")))
            missionPath = cwd / receivedPath / missionObj['path']
            ufName = f'{stuNum}-{students[stuNum]}.unconfirmed.{missionObj["ext"]}'
            if f and allowed_file(f.filename, {missionObj['ext']}):
                f.save(missionPath / ufName)
            return redirect(url_for('submit', missionurl=missionurl))
        resp = make_response(render_template(
            'submit.html', info=info, stuname=students[stuNum], missionObj=missionObj, missionStatus=missionStatus))
    return resp


@app.route('/lock/<missionurl>')
def lock(missionurl):
    stuNum = request.cookies.get("stun")
    missionObj = missionsDb[missionurl]
    missionStatus = genMissonStatus(stuNum, missionurl, missionObj)
    if stuNum not in students:
        resp = make_response(redirect(url_for('login', info="请先登录。")))
    else:
        if (missionStatus['status']) == '已提交':
            lockFile(stuNum, missionObj)
        resp = make_response(
            redirect(url_for('submit', missionurl=missionurl)))
    return resp


@app.route('/check/<missionurl>')
def check(missionurl):
    stuNum = request.cookies.get("stun")
    missionObj = missionsDb[missionurl]
    missionStatus = genMissonStatus(stuNum, missionurl, missionObj)
    if stuNum not in students:
        resp = make_response(redirect(url_for('login', info="请先登录。")))
    else:
        if (missionStatus['submitted']):
            if missionurl in checkersList:
                plugin = __import__(missionurl)
                checkerResult = plugin.check(missionStatus['currentFilePath'])
                resp = make_response(f'<!DOCTYPE html><html><body>{checkerResult}</body></html>')
            else:
                resp = make_response('<!DOCTYPE html><html><body></body></html>')
        else:
            resp = make_response('<!DOCTYPE html><html><body>未提交呢，请先提交。</body></html>')
    return resp


def allowed_file(filename, ALLOWED_EXTENSIONS):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def fileStatus(stuNum, missionBody):
    missionPath = cwd / receivedPath / missionBody['path']
    missionPath.mkdir(parents=True, exist_ok=True)
    ufName = f'{stuNum}-{students[stuNum]}.unconfirmed.{missionBody["ext"]}'
    cfName = f'{stuNum}-{students[stuNum]}.{missionBody["ext"]}'
    if ((missionPath / cfName).exists()):
        return ['已锁定', (missionPath / cfName).stat().st_size, datetime.fromtimestamp((missionPath / cfName).stat().st_mtime), (missionPath / cfName)]
    elif ((missionPath / ufName).exists()):
        return ['已提交', (missionPath / ufName).stat().st_size, datetime.fromtimestamp((missionPath / ufName).stat().st_mtime), (missionPath / ufName)]
    else:
        return ['未提交', 0, datetime.now(), None]


def lockFile(stuNum, missionBody):
    missionPath = cwd / receivedPath / missionBody['path']
    missionPath.mkdir(parents=True, exist_ok=True)
    ufName = f'{stuNum}-{students[stuNum]}.unconfirmed.{missionBody["ext"]}'
    cfName = f'{stuNum}-{students[stuNum]}.{missionBody["ext"]}'
    if ((missionPath / ufName).exists()):
        (missionPath / ufName).rename(missionPath / cfName)


def missionFinishRate(missionBody):
    missionPath = cwd / receivedPath / missionBody['path']
    missionPath.mkdir(parents=True, exist_ok=True)
    return 100 * len(list(missionPath.glob('*'))) / len(students)


def genMissonStatus(stuNum, missionUrl, missionBody):
    fs = fileStatus(stuNum, missionBody)
    result = {
        'name': missionBody['missionName'],
        'status': fs[0],
        'fileSize': fs[1],
        'subtime': fs[2].strftime(timeFormat),
        'due': datetime.fromisoformat(missionBody['dueDate']).strftime(timeFormat),
        "remain": datetime.fromisoformat(missionBody['dueDate']) - datetime.today(),
        'link': missionUrl,
        'finishrate': '%.2f' % missionFinishRate(missionBody),
        'currentFilePath': fs[3],
    }
    if result['status'] == '已锁定' or result['remain'].total_seconds() < 0:
        result['avaliable'] = False
    else:
        result['avaliable'] = True
    if result['status'] == '已锁定' or result['status'] == '已提交':
        result['submitted'] = True
    else:
        result['submitted'] = False
    return result


def genProgress(missionStatus):
    p = 0
    for i in missionStatus:
        if i['submitted']:
            p += 1
    return 100 * p / len(missionStatus)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
