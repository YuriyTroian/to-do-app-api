FROM python:3.11-slim


WORKDIR /fastapi

COPY ./requirements.txt /fastapi/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt


CMD ["uvicorn", "main:app", "--reload", "--port", "8000"]
