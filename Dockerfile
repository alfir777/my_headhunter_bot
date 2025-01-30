FROM python:3.12.8

RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean

RUN mkdir -p /home/user/web/config

RUN addgroup --system --gid 2000 user && adduser --system --uid 2000 user

ENV HOME=/home/user
ENV USER_HOME=/home/user/web/config
WORKDIR $USER_HOME

COPY ./pyproject.toml $USER_HOME/pyproject.toml
COPY ./poetry.lock $USER_HOME/poetry.lock

# set env variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip && pip install --upgrade setuptools
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-root

RUN chown -R user:user $USER_HOME

USER user