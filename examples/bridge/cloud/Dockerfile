FROM python:3.7

MAINTAINER joeymfaulkner@gmail.com

COPY examples/bridge/cloud/requirements.txt /cloud/requirements.txt

RUN pip install -r /cloud/requirements.txt

COPY examples/bridge/credentials/examples/*.der /credentials/
COPY examples/bridge/credentials/examples/cloud_private_key.pem /credentials/cloud_private_key.pem

COPY asyncua_utils /asyncua_utils/
COPY setup.py /asyncua_utils/setup.py

RUN python /asyncua_utils/setup.py install

ENV PYTHONPATH=.

COPY examples/bridge/cloud /cloud

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /wait
RUN chmod +x /wait

WORKDIR /cloud

CMD /wait && python cloud/forwarding-service.py