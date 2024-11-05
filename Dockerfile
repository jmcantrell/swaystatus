FROM docker.io/archlinux:latest
RUN pacman -Sy --noconfirm python python-pip

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN python -m venv venv
ENV PATH=./venv/bin:$PATH

RUN python -m pip install --upgrade pip

COPY requirements/ ./requirements/
RUN python -m pip install --no-cache-dir --requirement=./requirements/production.txt
RUN python -m pip install --no-cache-dir --requirement=./requirements/development.txt

COPY . .
RUN python -m pip install --no-cache-dir --editable=.
RUN ./scripts/test
