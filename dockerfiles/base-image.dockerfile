FROM python:3.6.13-slim-buster

RUN pip install cicadad==0.1.0
RUN python3 -c "import cicadad; print(cicadad.__file__)"
