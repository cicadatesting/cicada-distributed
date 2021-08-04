import base64
import json

CICADA_VERSION = "1.3.0"

DEFAULT_DOCKER_NETWORK = "cicada-distributed-network"
DEFAULT_KUBE_NAMESPACE = "default"
DOCKER_CONTAINER_MODE = "DOCKER"
KUBE_CONTAINER_MODE = "KUBE"
DEFAULT_CONTAINER_MODE = DOCKER_CONTAINER_MODE

DEFAULT_CONTEXT_STRING = base64.b64encode(json.dumps({}).encode("ascii")).decode(
    "ascii"
)

# METRICS_STREAM = "metrics"

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s -- %(message)s"
DATE_FORMAT = "%m-%d %H:%M"

DEFAULT_DATASTORE_ADDRESS = "cicada-distributed-datastore-client:8283"

DEFAULT_CONTAINER_SERVICE_ADDRESS = "cicada-distributed-container-service:8284"
