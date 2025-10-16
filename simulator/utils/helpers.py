"""
Helper functions for the simulator.
"""
import random


def generate_synthetic_trace(num_steps, workload_type, free_probability=0.3, lifetime_range=(5, 50)):
    """
    Generate a sequence of events with allocations and frees.

    Each event is a dict:
      - {'op': 'alloc', 'id': int, 'size': int}
      - {'op': 'free', 'id': int}

    We schedule frees for allocations after a random lifetime (within lifetime_range).
    free_probability is the fraction of allocated objects that are eligible to be freed before end.
    """
    trace = [None] * num_steps
    alloc_id = 0
    scheduled_frees = {}

    for t in range(num_steps):
        # Inject any scheduled frees for this time
        if t in scheduled_frees:
            # schedule frees at this time (may be multiple)
            for a_id in scheduled_frees[t]:
                trace[t] = {'op': 'free', 'id': a_id}
                # Only one event per step in this simple generator; if multiple scheduled, keep the last

        # If there's already a free scheduled at this step, sometimes also emit an alloc
        if trace[t] is None or random.random() < 0.5:
            # create an allocation event
            if workload_type == 'short':
                size = random.randint(1, 4)
            elif workload_type == 'long':
                size = random.randint(8, 32)
            else:
                size = random.randint(1, 32)

            trace[t] = {'op': 'alloc', 'id': alloc_id, 'size': size}

            # schedule a free for this allocation with some probability
            if random.random() < free_probability:
                lifetime = random.randint(lifetime_range[0], lifetime_range[1])
                free_time = min(num_steps - 1, t + lifetime)
                scheduled_frees.setdefault(free_time, []).append(alloc_id)

            alloc_id += 1

    # Any remaining scheduled frees that didn't get placed overwrite some allocs near the end
    for t, ids in scheduled_frees.items():
        for a_id in ids:
            if t < num_steps:
                trace[t] = {'op': 'free', 'id': a_id}

    return trace
