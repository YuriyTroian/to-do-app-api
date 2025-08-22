FROM python:3.11-slim


WORKDIR /fastapi

COPY ./requirements.txt /fastapi/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /fastapi


CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
