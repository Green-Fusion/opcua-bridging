FROM python:3.7

MAINTAINER joeymfaulkner@gmail.com

COPY examples/bridge/PLC/requirements.txt /server/requirements.txt

RUN pip install -r /server/requirements.txt

ENV PYTHONPATH=.

COPY asyncua_utils /asyncua_utils/
COPY setup.py /asyncua_utils/setup.py

RUN python /asyncua_utils/setup.py install

COPY examples/bridge/PLC /server

COPY examples/bridge/credentials/examples/*.der /credentials/
COPY examples/bridge/credentials/examples/PLC_private_key.pem /credentials/PLC_private_key.pem

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /wait
RUN chmod +x /wait

WORKDIR /server

CMD /wait && python PLC/unreliable_server.py