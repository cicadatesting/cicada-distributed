FROM cicadatesting/cicada-distributed-base-image:1.0.0

ENTRYPOINT ["python", "-u", "/usr/local/lib/python3.6/site-packages/cicadad/server/manager.py"]
