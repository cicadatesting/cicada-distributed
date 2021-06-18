FROM cicadatesting/cicada-distributed-base-image:pre-release

ENTRYPOINT ["python", "-u", "/usr/local/lib/python3.6/site-packages/cicadad/server/manager.py"]
