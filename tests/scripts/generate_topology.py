from random import uniform
from xlwt import easyxf, Workbook

wb = Workbook()
style0 = easyxf(
    'font: name Times New Roman, color-index black, bold on',
    num_format_str='#,##0.00'
)
style1 = easyxf(num_format_str='#,##0.00')

ws = wb.add_sheet('Device')

for index, header in enumerate(('name', 'longitude', 'latitude')):
    ws.write(0, index, header)
for i in range(1, 2000):
    for j in range(2):
        ws.write(i, j, str(i) if not j else uniform(1., 2.))
wb.save('test')
    