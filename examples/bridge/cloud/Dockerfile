FROM python:3.7

MAINTAINER joeymfaulkner@gmail.com

COPY cloud/requirements.txt /cloud/requirements.txt

RUN pip install -r /cloud/requirements.txt

COPY credentials/examples/*.der /credentials/
COPY credentials/examples/cloud_private_key.pem /credentials/cloud_private_key.pem

ENV PYTHONPATH=.

COPY cloud /cloud

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /wait
RUN chmod +x /wait

WORKDIR /cloud

CMD /wait && python cloud/forwarding_service.py