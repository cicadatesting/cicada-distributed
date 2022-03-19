from typing import Any
import base64
import json


def encode_context(context: Any) -> str:
    """Encode a context as a base64 string

    Args:
        context (any): Context object. Must be json serializable

    Returns:
        str: Encoded context base64 string
    """
    return base64.b64encode(json.dumps(context).encode("ascii")).decode("ascii")


def decode_context(encoded_context: str) -> Any:
    """Decode a base64 string to JSON deserialized context

    Args:
        encoded_context (str): Base64 context string

    Returns:
        any: Decoded context
    """
    decoded_context_bytes = base64.b64decode(
        encoded_context.encode("ascii"),
    )

    return json.loads(decoded_context_bytes.decode("ascii"))
