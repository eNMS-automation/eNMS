from sys import getsizeof

for variable in ("connections_cache", "service_db", "run_db", "run_logs"):
	print(f"{variable} memory usage: {getsizeof(getattr(app, variable))}")