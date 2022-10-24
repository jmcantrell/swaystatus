FROM docker.io/ubuntu:latest
RUN apt-get update -y
RUN apt-get install --no-install-recommends -y python3 python3-pip python3-venv

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN python3 -m venv venv
ENV PATH=./venv/bin:$PATH

COPY requirements*.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements/production.txt -r requirements/development.txt

COPY . .
RUN python3 -m pip install --no-cache-dir -e .
RUN pytest
