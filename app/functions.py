from .models import Device
import xlrd

def handle_uploaded_file(f):
    book = xlrd.open_workbook(file_contents=f.read())
    sheet = book.sheet_by_index(0)
    for row_index in range(1, sheet.nrows):
        keys = ('hostname', 'ip_address', 'vendor')
        values = sheet.row_values(row_index)
        Device.objects.create(**dict(zip(keys, values)))
