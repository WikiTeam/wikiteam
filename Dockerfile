FROM python:2.7-alpine

RUN mkdir /data
RUN mkdir /wikiteam
ADD . /wikiteam
WORKDIR /wikiteam
RUN pip install --upgrade -r requirements.txt

VOLUME /data
