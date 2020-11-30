# Uses the "pympler" module for profiling memory.

from operator import itemgetter
from pympler import muppy, summary

MODULES = ["netmiko", "napalm", "sqlalchemy"]

profile = sorted(
    (
        object_
        for object_ in summary.summarize(muppy.get_objects())
        if any(module in object_[0] for module in MODULES)
    ),
    key=itemgetter(2),
    reverse=True
)

for object_ in profile:
    print(f"Name: {object_[0]}")
    print(f"Number of objects: {object_[1]}")
    print(f"Total size: {object_[2]}")
