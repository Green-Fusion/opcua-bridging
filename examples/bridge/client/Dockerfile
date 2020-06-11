FROM python:3.7

MAINTAINER joeymfaulkner@gmail.com

COPY client/requirements.txt /client/requirements.txt

RUN pip install -r /client/requirements.txt

ENV PYTHONPATH=.

COPY client /client

COPY credentials/examples/*.der /credentials/
COPY credentials/examples/user_admin_private_key.pem /credentials/user_admin_private_key.pem

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /wait
RUN chmod +x /wait

WORKDIR /client

CMD /wait && python client/end_client.py