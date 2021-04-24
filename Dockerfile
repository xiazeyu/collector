FROM tiangolo/meinheld-gunicorn-flask

COPY ./app /app

RUN pip install --no-cache-dir -r /app/requirements.txt
