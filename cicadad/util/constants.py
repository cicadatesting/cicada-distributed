import base64
import json

CICADA_VERSION = "1.6.0"

DEFAULT_DOCKER_NETWORK = "cicada-distributed-network"
DEFAULT_KUBE_NAMESPACE = "default"
LOCAL_SCHEDULING_MODE = "LOCAL"
DOCKER_SCHEDULING_MODE = "DOCKER"
KUBE_SCHEDULING_MODE = "KUBE"
DEFAULT_SCHEDULING_MODE = LOCAL_SCHEDULING_MODE

DEFAULT_CONTEXT_STRING = base64.b64encode(json.dumps({}).encode("ascii")).decode(
    "ascii"
)

# METRICS_STREAM = "metrics"

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s -- %(message)s"
DATE_FORMAT = "%m-%d %H:%M"

LOCALHOST_BACKEND_ADDRESS = "[::]:8283"
CONTAINER_BACKEND_ADDRESS = "cicada-distributed-backend:8283"

DEFAULT_BACKEND_ADDRESS = LOCALHOST_BACKEND_ADDRESS

ONE_SEC_MS = 1000
