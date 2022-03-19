from typing import Any, Callable
import time


def exponential_backoff(
    get_client_fn: Callable[[], Any],
    error_class: Any,
    tries: int,
    initial_wait: int = 2,
    multiplier: int = 2,
):
    """Get a client using an exponential backoff

    Args:
        get_client_fn (Callable): Function to get client.
        error_class (Any): Class to check exceptions against to determine if it should retry.
        tries (int): Number of attempts allowed to get client.
        initial_wait (int, optional): Time in seconds for first wait after a failure. Defaults to 2.
        multiplier (int, optional): Amount to multiply wait time by after each failure. Defaults to 2.

    Raises:
        e: Exception if not an instance of error_class.
        RuntimeError: Exhausted retries.

    Returns:
        Any: Client if successfully configured
    """
    remaining_tries = tries
    wait = initial_wait

    while remaining_tries > 0:
        try:
            return get_client_fn()
        except Exception as e:
            if isinstance(e, error_class):
                time.sleep(wait)

                remaining_tries -= 1
                wait *= multiplier
            else:
                raise e

    raise RuntimeError(f"Timed out waiting for client: {get_client_fn}")
