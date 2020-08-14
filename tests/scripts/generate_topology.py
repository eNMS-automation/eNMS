from pathlib import Path
from random import randrange, uniform
from xlwt import easyxf, Workbook

DEVICE_HEAHDERS = ("name", "longitude", "latitude", "subtype", "ip_address")
LINK_HEADERS = ("name", "source_name", "destination_name", "color")

workbook = Workbook()
style0 = easyxf(
    "font: name Times New Roman, color-index black, bold on", num_format_str="#,##0.00"
)
style1 = easyxf(num_format_str="#,##0.00")

device_sheet = workbook.add_sheet("device")
link_sheet = workbook.add_sheet("link")

for index, header in enumerate(DEVICE_HEAHDERS):
    device_sheet.write(0, index, header)

for index, header in enumerate(LINK_HEAHDERS):
    link_sheet.write(0, index, header)

for index in range(1, 9000):
    device_sheet.write(index, 0, f"d{index}")
    device_sheet.write(index, 1, uniform(-180.0, 180.0))
    device_sheet.write(index, 2, uniform(-90.0, 90.0))
    device_sheet.write(index, 3, "router")
    device_sheet.write(index, 4, f"d{index}")
    source, destination = randrange(9000), randrange(9000)
    link_sheet.write(index, 0, f"d{source}-d{destination}")
    link_sheet.write(index, 1, f"d{source}")
    link_sheet.write(index, 2, f"d{destination}")
    link_sheet.write(index, 3, f"#{hex(randrange(16777215))[2:]}")

workbook.save(Path.cwd() / "test_65000.xls")
