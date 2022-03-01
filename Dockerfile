FROM python:3.9

RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean

RUN mkdir -p /home/user/web/config

RUN addgroup --system --gid 2000 user && adduser --system --uid 2000 user

ENV HOME=/home/user
ENV USER_HOME=/home/user/web/config
WORKDIR $USER_HOME

COPY ./requirements.txt $HOME

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
RUN pip install -r $HOME/requirements.txt

RUN chown -R user:user $USER_HOME

USER user