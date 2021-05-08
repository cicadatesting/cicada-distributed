FROM python:3.6.13-slim-buster

RUN pip install --user --upgrade setuptools wheel
RUN pip install docker \
    click \
    pydantic \
    kafka-python \
    grpcio \
    protobuf

COPY dist dist
COPY build build
# COPY src/cicadad.egg-info src/cicadad-egg-info
COPY setup.py .
# COPY setup.cfg .
# COPY pyproject.toml .
# COPY MANIFEST.in .

# RUN python3 -c "import cicadad; print(cicadad.__file__)"
RUN python setup.py install
