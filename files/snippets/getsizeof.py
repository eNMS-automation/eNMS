# This script monitors the memory usage of a few controller variables used
# for storing data, like the network connections cache (stores netmiko,
# napalm and scrapli connections) and the logs cache (stores service logs).
# Memory usage of these variables should not grow over time are their content
# is supposed to be deleted when no longer useful.
# flake8: noqa

from sys import getsizeof

VARIABLES = {
    "connections_cache": "Network Connections Cache",
    "service_run_count": "Service Run cache",
    "run_states": "Run State Cache",
    "run_logs": "Run Logs Cache",
}

print("MEMORY USAGE :", end="\n\n")
for variable, function in VARIABLES.items():
    size = getsizeof(getattr(app, variable))
    print(f"{function} ({variable}): {size} bytes")
