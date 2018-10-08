from pathlib import Path
from random import uniform
from xlwt import easyxf, Workbook

wb = Workbook()
style0 = easyxf(
    'font: name Times New Roman, color-index black, bold on',
    num_format_str='#,##0.00'
)
style1 = easyxf(num_format_str='#,##0.00')

ws = wb.add_sheet('Device')

for index, header in enumerate(('name', 'longitude', 'latitude', 'subtype')):
    ws.write(0, index, header)

for i in range(1, 1000):
    ws.write(i, 0, i)
    ws.write(i, 1, uniform(-40., 40.))
    ws.write(i, 2, uniform(-40., 40.))
    ws.write(i, 3, 'router')

wb.save(Path.cwd() / 'test.xls')
