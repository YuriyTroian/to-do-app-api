FROM python:3.11-slim

RUN useradd -m -r appuser

WORKDIR /fastapi

COPY ./requirements.txt /fastapi/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /fastapi

RUN chown -R appuser:appuser /fastapi

USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]