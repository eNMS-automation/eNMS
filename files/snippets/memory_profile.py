# Uses the "pympler" module for profiling memory.

from pympler import muppy, summary

MODULES = ["netmiko", "napalm"]

profile = summary.summarize(muppy.get_objects())

for object_ in profile:
    if any(module in object_[0] for module in MODULES):
        print("{}: {} objects | size: {} bytes".format(*object_))