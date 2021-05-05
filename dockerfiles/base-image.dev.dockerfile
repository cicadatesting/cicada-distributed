FROM python:3.6.13-slim-buster

RUN pip install docker \
    click \
    pydantic \
    kafka-python \
    grpcio \
    protobuf

# RUN python3 -c "import cicadad; print(cicadad.__file__)"
RUN python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps cicadad==0.0.6
