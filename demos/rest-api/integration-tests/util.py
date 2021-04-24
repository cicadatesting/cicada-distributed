from datetime import timedelta


def post_user_aggregator(previous, latest_results):
    failures = 0
    successes = 0
    previous_timestamps = []

    if previous is not None:
        failures = previous["failures"]
        successes = previous["successes"]
        previous_timestamps = previous["timestamps"]

    timestamps = []

    for result in latest_results:
        if result.exception is not None:
            failures += 1
        else:
            successes += 1

        timestamps.append(result.timestamp)

    sorted_timestamps = sorted(timestamps)

    combined_timestamps = previous_timestamps + sorted_timestamps
    filtered_timestamps = []

    if combined_timestamps != []:
        last_timestamp = combined_timestamps[-1]

        for timestamp in combined_timestamps:
            if timestamp >= last_timestamp - timedelta(seconds=1):
                filtered_timestamps.append(timestamp)

    return {
        "failures": failures,
        "successes": successes,
        "responses_per_second": len(filtered_timestamps),
        "timestamps": filtered_timestamps,
    }


def print_get_user_output(aggregate):
    if aggregate is not None:
        return f"""
        * Failures: {aggregate['failures']}
        * Successes: {aggregate['successes']}
        * Responses Per Second: {aggregate['responses_per_second']}
        """
