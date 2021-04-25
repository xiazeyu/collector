from typing import Optional

from fastapi import FastAPI


app = FastAPI()


@app.get('/')
@app.get('/login')
async def login(stu_id: Optional[str] = None):
    """
    Display the login page.

    Args:
        stu_id: the identification of a student

    Returns:
        some type: the response body
    """
    if stu_id:
        return {"toshow": "login page"}
    else:
        return {"toshow": "do login process"}


@app.get('/logout')
async def logout():
    """
    Let user logout(clear the cookie).

    Args:
        None

    Returns:
        some type: the response body
    """
    return {"status": "to be done"}


@app.get('/submit')
async def submit_list():
    """
    Display the missions page.

    Args:
        None

    Returns:
        some type: the response body
    """
    return {"status": "to be done"}


@app.get('/submit/{missionurl}')
async def submit_detailed(missionurl: str):
    """
    Display the submit page.

    Args:
        missionurl: the url-name of the mission

    Returns:
        some type: the response body
    """
    return {"status": "to be done", "missionurl": missionurl}


@app.post('/submit/{missionurl}')
async def submit_handler(missionurl: str):
    """
    Handle the submission.

    Args:
        missionurl: the url-name of the mission

    Returns:
        some type: the response body
    """
    return {"status": "to be done", "missionurl": missionurl}


@app.get('/lock/{missionurl}')
async def lock(missionurl: str):
    """
    Lock the uploaded file.

    Args:
        missionurl: the url-name of the mission

    Returns:
        some type: the response body
    """
    return {"status": "to be done", "missionurl": missionurl}


@app.get('/check/{missionurl}')
async def check(missionurl: str):
    """
    Display check of the uploaded file.

    Args:
        missionurl: the url-name of the mission

    Returns:
        some type: the response body
    """
    return {"status": "to be done", "missionurl": missionurl}
