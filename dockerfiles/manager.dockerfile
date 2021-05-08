FROM cicadatesting/cicada-distributed-base-image:0.1.1

RUN pip install dask \
    distributed

ENTRYPOINT ["python", "-u", "/usr/local/lib/python3.6/site-packages/cicadad/server/manager.py"]
