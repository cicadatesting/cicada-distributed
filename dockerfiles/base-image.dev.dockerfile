FROM python:3.6.13-slim-buster

WORKDIR /cicada-distributed

COPY requirements.txt .

RUN pip install -r requirements.txt
RUN pip install --user --upgrade setuptools wheel

COPY dist dist
COPY build build
# COPY src/cicadad.egg-info src/cicadad-egg-info
COPY setup.py .
# COPY setup.cfg .
# COPY pyproject.toml .
# COPY MANIFEST.in .

# RUN python3 -c "import cicadad; print(cicadad.__file__)"
RUN python setup.py install
