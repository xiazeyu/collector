FROM tiangolo/uvicorn-gunicorn-fastapi
COPY ./app /app
RUN pip install --no-cache-dir -r /app/requirements.txt && pip install --upgrade jinja2