FROM python:3.6.13-slim-buster


WORKDIR /cicada-distributed

COPY requirements.txt .

RUN pip install -r requirements.txt

# NOTE: comment/uncomment to install from pypi
# RUN pip install -i https://test.pypi.org/simple/ cicadad

COPY cicadad cicadad
COPY setup.cfg .
COPY setup.py .

RUN python3 -m pip install -e .
