FROM python:3.9-slim-buster

WORKDIR /backend

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

RUN apt-get update \
    && apt-get -y install netcat gcc default-libmysqlclient-dev \
    && apt-get clean

RUN pip install --upgrade pip
RUN pip install poetry && poetry config virtualenvs.create false

COPY ./pyproject.toml ./
RUN poetry install --no-root

COPY . .
RUN poetry install -E mysql
