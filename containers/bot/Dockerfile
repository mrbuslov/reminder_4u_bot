FROM python:3.11.6-bullseye

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/ukrainian-scientists-platform/backend

RUN mkdir /core
WORKDIR /core

COPY ./requirements.txt .
COPY ./bot .

RUN pip install -r ./requirements.txt
