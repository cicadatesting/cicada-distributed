FROM python:3.6.13-slim-buster


WORKDIR /cicada-distributed

RUN pip install docker \
    click \
    pydantic \
    kafka-python \
    grpcio \
    protobuf

# NOTE: comment/uncomment to install from pypi
# RUN pip install -i https://test.pypi.org/simple/ cicadad

COPY src/cicadad src/cicadad
COPY setup.cfg .
COPY setup.py .
# TODO: need a production version of the base image

RUN python3 -m pip install -e .
