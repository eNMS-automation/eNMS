from collections import Counter
from pathlib import Path
from random import choice, randrange, uniform
from xlwt import easyxf, Workbook

DEVICE_HEAHDERS = ("name", "longitude", "latitude", "icon", "ip_address")
LINK_HEADERS = ("name", "source_name", "destination_name", "color")
DEVICE_TYPES = (
    "antenna",
    "firewall",
    "host",
    "optical_switch",
    "regenerator",
    "router",
    "server",
    "site",
    "switch",
)

workbook = Workbook()
style0 = easyxf(
    "font: name Times New Roman, color-index black, bold on", num_format_str="#,##0.00"
)
style1 = easyxf(num_format_str="#,##0.00")

device_sheet = workbook.add_sheet("device")
link_sheet = workbook.add_sheet("link")

for index, header in enumerate(DEVICE_HEAHDERS):
    device_sheet.write(0, index, header)

for index, header in enumerate(LINK_HEADERS):
    link_sheet.write(0, index, header)

for index in range(1, 2000):
    device_sheet.write(index, 0, f"d{index}")
    device_sheet.write(index, 1, uniform(-180.0, 180.0))
    device_sheet.write(index, 2, uniform(-90.0, 90.0))
    device_sheet.write(index, 3, choice(DEVICE_TYPES))
    device_sheet.write(index, 4, f"d{index}")

device_counter = Counter()
for index in range(1, 3000):
    source, destination = randrange(1, 2000), randrange(1, 2000)
    device_counter[f"d{source}-d{destination}"] += 1
    number = device_counter[f"d{source}-d{destination}"]
    link_sheet.write(index, 0, f"d{source}-d{destination}-{number}")
    link_sheet.write(index, 1, f"d{source}")
    link_sheet.write(index, 2, f"d{destination}")
    link_sheet.write(index, 3, f"#{hex(randrange(16777215))[2:]}")

workbook.save(Path.cwd() / "topology_2000_nodes_3000_links.xls")
