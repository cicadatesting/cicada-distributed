FROM cicadatesting/cicada-distributed-base-image:pre-release

COPY . .

ENTRYPOINT ["python", "-u", "test.py"]
