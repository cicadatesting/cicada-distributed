
FROM python:3.8-buster

WORKDIR /app

RUN apt-get update
RUN apt-get install -y python3-dev build-essential libpq-dev

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

EXPOSE 8080
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
