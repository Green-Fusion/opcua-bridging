FROM python:3.7

MAINTAINER joeymfaulkner@gmail.com

COPY PLC/requirements.txt /server/requirements.txt

RUN pip install -r /server/requirements.txt

ENV PYTHONPATH=.

COPY PLC /server

COPY credentials/examples/*.der /credentials/
COPY credentials/examples/PLC_private_key.pem /credentials/PLC_private_key.pem

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /wait
RUN chmod +x /wait

WORKDIR /server

CMD /wait && python PLC/server.py