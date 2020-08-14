from pathlib import Path
from random import uniform
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

for i in range(1, 9000):
    device_sheet.write(i, 0, "a" + str(i))
    device_sheet.write(i, 1, uniform(-180.0, 180.0))
    device_sheet.write(i, 2, uniform(-90.0, 90.0))
    device_sheet.write(i, 3, "router")
    device_sheet.write(i, 4, "a" + str(i))

workbook.save(Path.cwd() / "test_65000.xls")
