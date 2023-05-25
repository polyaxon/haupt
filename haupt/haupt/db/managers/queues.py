from typing import Optional


def get_num_to_start(concurrency: int, consumed: int, max_budget: Optional[int]) -> int:
    """We need to check if we are allowed to start the experiment
    If the polyaxonfile has concurrency we need to check how many experiments are running.

    N.B. max_budget is set ~ inf
    """
    if concurrency is None or concurrency < 0:  # We max all runs
        concurrency = max_budget
        max_budget = None

    if concurrency is None:
        return 0

    if max_budget is None:  # No budget only check concurrency
        # Target to start: should try to always schedule to the target concurrency
        return concurrency - consumed

    if max_budget <= 0:  # Not allowed to start anything
        return 0

    if (
        max_budget and max_budget <= consumed
    ):  # Already consumed the max possible budget
        return 0

    # Either respect the concurrency settings or the allocatable budget if the budget is smaller
    max_to_start = max_budget - consumed

    # Target to start: should try to always schedule to the target concurrency
    target = concurrency - consumed

    return target if target < max_to_start else max_to_start
