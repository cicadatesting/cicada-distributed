FROM cicadatesting/cicada-distributed-base-image:latest

RUN pip install dask \
    distributed

ENTRYPOINT ["python", "-u", "/cicada-distributed/src/cicadad/server/manager.py"]
