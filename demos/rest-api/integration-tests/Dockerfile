FROM cicadatesting/cicada-distributed-base-image:latest

RUN pip install requests

COPY . .

ENTRYPOINT ["python", "-u", "example.py"]

# Pass command to start a user:
# CMD ["run-user", "get_user"]
