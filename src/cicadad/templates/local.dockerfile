FROM cicadatesting/cicada-distributed-base-image:latest

COPY . .

ENTRYPOINT ["python", "-u", "test.py"]
