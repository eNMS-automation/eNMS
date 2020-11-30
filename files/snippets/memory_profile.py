# Uses the "pympler" module for profiling memory.

from pympler import muppy, summary

profile = summary.summarize(muppy.get_objects())
summary.print_(profile, limit=100)
