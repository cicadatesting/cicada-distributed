FROM cicadatesting/cicada-distributed-base-image:latest

ENTRYPOINT ["python", "-u", "/cicada-distributed/src/cicadad/server/manager.py"]
