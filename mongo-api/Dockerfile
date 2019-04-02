FROM python:3.7-alpine 

WORKDIR /mongo-api
COPY requirements.txt /mongo-api

RUN pip install -r requirements.txt
#ENTRYPOINT gunicorn app:app -b 0.0.0.0:3386
