FROM cicadatesting/cicada-distributed-base-image:pre-release

RUN pip install dask \
    distributed

ENTRYPOINT ["python", "-u", "/usr/local/lib/python3.6/site-packages/cicadad/server/manager.py"]
