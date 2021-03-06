FROM python:3.6.13-slim-buster

ARG CICADA_VERSION
WORKDIR /cicada-distributed

COPY requirements.txt .

RUN pip install -r requirements.txt

# RUN python3 -c "import cicadad; print(cicadad.__file__)"
RUN python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps cicadad==$CICADA_VERSION
