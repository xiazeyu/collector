FROM tiangolo/uvicorn-gunicorn-fastapi
ENV PRODUCTION=1
COPY ./app /app
RUN pip install --no-cache-dir -r /app/requirements.txt