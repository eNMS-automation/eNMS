# Uses the "pympler" module for profiling memory.
# By default, objects are sorted by their size in memory.
# The order can be changed to sorting by number of objects in
# memory by replacing "itemgetter(2)" with "itemgetter(1)".
# The "MAX_RESULTS" variable limits the output to the first
# MAX_RESULTS results.

# flake8: noqa

from operator import itemgetter
from pympler import muppy, summary

MODULES = ["netmiko", "napalm", "sqlalchemy"]
MAX_RESULTS = 50

all_objects = muppy.get_objects()


def format_size(size):
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if size < 1024.0 or unit == "GiB":
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"


profile = sorted(
    (object_ for object_ in summary.summarize(all_objects)),
    key=itemgetter(2),
    reverse=True,
)

for object_ in profile[:MAX_RESULTS]:
    print(f"Name: {object_[0]}")
    print(f"Number of objects: {object_[1]}")
    print(f"Total size: {format_size(object_[2])}", end="\n\n")


for type in (str, dict):
    print(f"Last {MAX_RESULTS} {type} objects in memory", end="\n\n")
    print("\n".join(muppy.filter(all_objects, Type=type)[-MAX_RESULTS:]))
