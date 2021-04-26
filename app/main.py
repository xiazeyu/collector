from datetime import datetime
from typing import Optional

from fastapi import Cookie, Depends, FastAPI, Request, File, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import config
from store import Store, Student, MissionStatus, StatusEnum

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

store = Store()


def encode_cookies(string_to_encode: str) -> str:
    """
    Decode the utf-8 string, and encode it to latin-1.

    Args:
        string_to_encode: string to encode

    Returns:
        str: encoded string
    """
    return string_to_encode.encode('utf-8').decode('latin-1')


def decode_cookies(string_to_decode: Optional[str] = None) -> Optional[str]:
    """
    Decode the latin-1 string, and encode it to utf-8.

    Args:
        string_to_decode: string to decode

    Returns:
        Optional[str]: decoded string
    """
    if string_to_decode:
        return string_to_decode.encode('latin-1').decode('utf-8')
    return None


def get_stu_id(stu_id: Optional[str] = None,
               stu_id_cookie: Optional[str] = Cookie(None)) -> Optional[str]:
    """
    Get student id from client.

    Args:
        stu_id: student id from query string
        stu_id_cookie: student id from cookie

    Returns:
        Optional[str]: student id
    """
    if config.DEBUG_FLAG:
        print({'stu_id': stu_id, 'stu_id_cookie': stu_id_cookie})
    return stu_id_cookie or stu_id


def check_stu_id(stu_id: Optional[str] = Depends(get_stu_id)) -> bool:
    """
    Check if student id is valid.

    Args:
        stu_id: student id

    Returns:
        bool: if student id is valid
    """
    result = stu_id in store.students
    if config.DEBUG_FLAG:
        print({'stu_id': stu_id, 'check_stu_id': result})
    return result


def invalid_response(valid_logon: Optional[bool] = Depends(check_stu_id)) -> Optional[HTMLResponse]:
    """
    Generate the response of invalid logon if so.

    Args:
        valid_logon: whether current logon is valid

    Returns:
        Optional[HTMLResponse]: response
    """
    if valid_logon:
        return None
    response = RedirectResponse('/', status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key='info', value=encode_cookies('请先登录。'))
    return response


def get_stu_obj(stu_id: Optional[str] = Depends(get_stu_id)) -> Student:
    """
    Get student obj.
    Need to run invalid_response first.

    Args:
        stu_id: student id

    Returns:
        Student: student obj
    """
    stu_obj = Student(stu_id=stu_id, name=store.students[stu_id])
    if config.DEBUG_FLAG:
        print({'stu_obj': stu_obj})
    return stu_obj


@app.get('/', response_class=HTMLResponse)
@app.get('/login', response_class=HTMLResponse)
async def login(request: Request,
                stu_id: Optional[str] = Depends(get_stu_id),
                info: Optional[str] = Cookie(None)) -> HTMLResponse:
    """
    Display the login page.

    Args:
        request: request from client
        stu_id: provided student id
        info: notification from cookie

    Returns:
        HTMLResponse: the response body
    """
    if stu_id:
        if check_stu_id(stu_id):
            response = RedirectResponse(
                '/submit', status_code=status.HTTP_302_FOUND)
            response.set_cookie(key='stu_id_cookie',
                                value=stu_id, max_age=2592000)
        else:
            response = RedirectResponse(
                '/', status_code=status.HTTP_303_SEE_OTHER)
            response.delete_cookie(key='stu_id_cookie')
            response.set_cookie(
                key='info', value=encode_cookies('您的学号有误。请核对后再试。'))
    else:
        response = templates.TemplateResponse(
            "login.html", {'request': request, 'info': decode_cookies(info)})

    if info:
        response.delete_cookie(key='info')

    return response


@app.get('/logout', response_class=HTMLResponse)
async def logout() -> HTMLResponse:
    """
    Let user logout(clear the cookie).

    Args:
        None

    Returns:
        HTMLResponse: the response body
    """
    response = RedirectResponse('/', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key='stu_id_cookie')
    response.set_cookie(key='info', value=encode_cookies('已登出。'))
    return response


@app.get('/submit', response_class=HTMLResponse)
async def submit_list(request: Request,
                      stu_id: Optional[str] = Depends(get_stu_id),
                      invalid: Optional[HTMLResponse] = Depends(invalid_response)) -> HTMLResponse:
    """
    Display the missions page.

    Args:
        request: request from client
        stu_id: provided student id
        invalid: response when session is invalid

    Returns:
        HTMLResponse: the response body
    """
    if invalid:
        return invalid
    stu_obj = get_stu_obj(stu_id)
    missions_status = []
    submitted = 0
    for key in sorted(store.missions.keys()):
        mission_status = MissionStatus(student=stu_obj,
                                       mission=store.missions[key],
                                       stu_count=len(store.students))
        missions_status.append(await mission_status.fetch())
        if mission_status.submitted:
            submitted += 1
    if config.DEBUG_FLAG:
        print(missions_status)
    return templates.TemplateResponse(
        'missions.html', {'request': request,
                          'student': stu_obj,
                          'missions_status': missions_status,
                          'now': datetime.today().strftime(config.DATETIME_FORMAT),
                          'progress': 100 * submitted / len(store.missions)})


@app.get('/submit/{mission_url}', response_class=HTMLResponse)
async def submit_detailed(request: Request,
                          mission_url: str,
                          stu_id: Optional[str] = Depends(get_stu_id),
                          invalid: Optional[HTMLResponse] = Depends(
                              invalid_response),
                          info: Optional[str] = Cookie(None)) -> HTMLResponse:
    """
    Display the submit page.

    Args:
        request: request from client
        mission_url: the url-name of the mission
        stu_id: provided student id
        invalid: response when session is invalid
        info: notification from cookie

    Returns:
        HTMLResponse: the response body
    """
    if invalid:
        return invalid
    stu_obj = get_stu_obj(stu_id)

    mission_status = await MissionStatus(student=stu_obj,
                                         mission=store.missions[mission_url],
                                         stu_count=len(store.students)).fetch()

    response = templates.TemplateResponse(
        "submit.html", {'request': request,
                        'info': decode_cookies(info),
                        'mission_status': mission_status})
    if info:
        response.delete_cookie(key='info')
    return response


def allowed_file(file: UploadFile, allowed_extension: str) -> bool:
    """
    Check if the filename has allowed extension.

    Args:
        file: file uploaded
        allowed_extension: extension allowed

    Returns:
        bool: if the filename has allowed extension
    """
    filename = file.filename
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() == allowed_extension


@app.post('/submit/{mission_url}', response_class=HTMLResponse)
async def submit_handler(mission_url: str,
                         file: UploadFile = File(...),
                         stu_id: Optional[str] = Depends(get_stu_id),
                         invalid: Optional[HTMLResponse] = Depends(
                             invalid_response)) -> HTMLResponse:
    """
    Handle the submission.

    Args:
        mission_url: the url-name of the mission
        file: uploaded file
        stu_id: provided student id
        invalid: response when session is invalid

    Returns:
        HTMLResponse: the response body
    """
    if invalid:
        return invalid
    stu_obj = get_stu_obj(stu_id)

    mission_status = await MissionStatus(student=stu_obj,
                                         mission=store.missions[mission_url],
                                         stu_count=len(store.students)).fetch()
    ext = mission_status.mission.ext

    response = RedirectResponse(
        url=f'/submit/{mission_url}', status_code=status.HTTP_303_SEE_OTHER)

    if not mission_status.avaliable:
        response.set_cookie(
            key='info', value=encode_cookies('当前任务已无法提交。'))
        return response

    if not allowed_file(file=file, allowed_extension=ext):
        response.set_cookie(
            key='info', value=encode_cookies(f'请上传{ext}格式的文件。'))
        return response

    try:
        mission_path = config.received_path / mission_status.mission.subpath
        ucfp = mission_path / f'{stu_obj.stu_id}-{stu_obj.name}.unconfirmed.{ext}'

        up_stream = await file.read(mission_status.mission.size)
        with open(ucfp, "wb") as target:
            target.write(up_stream)
        target.close()
    except:  # pylint: disable=bare-except
        response.set_cookie(
            key='info', value=encode_cookies('上传失败，请联系管理员。'))
        return response

    response.set_cookie(
        key='info', value=encode_cookies('上传成功。'))

    return response


@app.get('/lock/{mission_url}', response_class=HTMLResponse)
async def lock(mission_url: str,
               stu_id: Optional[str] = Depends(get_stu_id),
               invalid: Optional[HTMLResponse] = Depends(
                   invalid_response)) -> HTMLResponse:
    """
    Lock the uploaded file.

    Args:
        mission_url: the url-name of the mission
        stu_id: provided student id
        invalid: response when session is invalid

    Returns:
        HTMLResponse: the response body
    """
    if invalid:
        return invalid
    stu_obj = get_stu_obj(stu_id)

    mission_status = await MissionStatus(student=stu_obj,
                                         mission=store.missions[mission_url],
                                         stu_count=len(store.students)).fetch()
    ext = mission_status.mission.ext

    response = RedirectResponse(
        url=f'/submit/{mission_url}', status_code=status.HTTP_303_SEE_OTHER)

    if mission_status.status == StatusEnum.UPLOADED:
        mission_path = config.received_path / mission_status.mission.subpath
        ucfp = mission_path / f'{stu_obj.stu_id}-{stu_obj.name}.unconfirmed.{ext}'
        ccfp = mission_path / f'{stu_obj.stu_id}-{stu_obj.name}.{ext}'
        if ucfp.exists():
            ucfp.rename(mission_path / ccfp)
        response.set_cookie(
            key='info', value=encode_cookies('锁定成功。'))

    return response


@app.get('/check/{mission_url}', response_class=HTMLResponse)
async def check(mission_url: str,
                stu_id: Optional[str] = Depends(get_stu_id),
                invalid: Optional[HTMLResponse] = Depends(
                    invalid_response)) -> HTMLResponse:
    """
    Display check of the uploaded file.

    Args:
        mission_url: the url-name of the mission
        stu_id: provided student id
        invalid: response when session is invalid

    Returns:
        HTMLResponse: the response body
    """
    if invalid:
        return invalid
    stu_obj = get_stu_obj(stu_id)

    mission_status = await MissionStatus(student=stu_obj,
                                         mission=store.missions[mission_url],
                                         stu_count=len(store.students)).fetch()

    if mission_status.submitted and mission_url in store.checkers:
        response = HTMLResponse(
            content=store.checkers[mission_url](mission_status.sub_file_path))
        return response
    return None
