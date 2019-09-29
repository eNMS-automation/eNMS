from pathlib import Path
from random import uniform
from xlwt import easyxf, Workbook

wb = Workbook()
style0 = easyxf(
    "font: name Times New Roman, color-index black, bold on", num_format_str="#,##0.00"
)
style1 = easyxf(num_format_str="#,##0.00")

ws = wb.add_sheet("device")

for index, header in enumerate(
    ("name", "longitude", "latitude", "subtype", "ip_address")
):
    ws.write(0, index, header)

for i in range(1, 65000):
    ws.write(i, 0, "a" + str(i))
    ws.write(i, 1, uniform(-180.0, 180.0))
    ws.write(i, 2, uniform(-90.0, 90.0))
    ws.write(i, 3, "router")
    ws.write(i, 4, "a" + str(i))

wb.save(Path.cwd() / "test_65000.xls")
