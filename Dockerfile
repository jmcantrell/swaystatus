FROM docker.io/ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python3 python3-pip python3-venv

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN python3 -m venv venv
ENV PATH=./venv/bin:$PATH

COPY requirements*.txt ./
RUN python3 -m pip install -r requirements.txt -r requirements_dev.txt

COPY . .
RUN python3 -m pip install -e .
RUN pytest
