FROM python:3.6.13-slim-buster

ARG CICADA_VERSION

RUN pip install cicadad==$CICADA_VERSION
