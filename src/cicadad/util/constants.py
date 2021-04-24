import base64
import json

CONTAINERS_STREAM = "containers"
DEFAULT_EVENT_ADDRESS = "cicada-distributed-kafka:9092"
DEFAULT_EVENT_POLLING_MS = 1000
DEFAULT_MAX_EVENTS = 500

DEFAULT_DOCKER_NETWORK = "cicada-distributed-network"

DEFAULT_CONTEXT_STRING = base64.b64encode(json.dumps({}).encode("ascii")).decode(
    "ascii"
)

# METRICS_STREAM = "metrics"

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s -- %(message)s"
DATE_FORMAT = "%m-%d %H:%M"
