from logging import info
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS.main import db
from eNMS.base.helpers import delete_all, factory, fetch_all, serialize
from eNMS.base.properties import export_properties


def database_filtering(pool):
    pool_objects = {'Device': pool.devices, 'Link': pool.links}
    for obj_type in ('Device', 'Link'):
        for obj in fetch_all(obj_type):
            setattr(obj, 'hidden', obj not in pool_objects[obj_type])
    db.session.commit()


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


def object_import(request, file):
    if request['replace']:
        delete_all('Device')
    result = 'Topology successfully imported.'
    if allowed_file(secure_filename(file.filename), {'xls', 'xlsx'}):
        book = open_workbook(file_contents=file.read())
        for obj_type in ('Device', 'Link'):
            try:
                sheet = book.sheet_by_name(obj_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                prop = dict(zip(properties, sheet.row_values(row_index)))
                try:
                    factory(obj_type, **prop).serialized
                except Exception as e:
                    info(f'{str(prop)} could not be imported ({str(e)})')
                    result = 'Partial import (see logs).'
            db.session.commit()
    if request['update_pools']:
        for pool in fetch_all('Pool'):
            pool.compute_pool()
        db.session.commit()
    return result


def object_export(request, path_app):
    workbook = Workbook()
    for obj_type in ('Device', 'Link'):
        sheet = workbook.add_sheet(obj_type)
        for index, property in enumerate(export_properties[obj_type]):
            sheet.write(0, index, property)
            for obj_index, obj in enumerate(serialize(obj_type), 1):
                sheet.write(obj_index, index, obj[property])
    workbook.save(path_app / 'projects' / f'{request["name"]}.xls')
    return True
