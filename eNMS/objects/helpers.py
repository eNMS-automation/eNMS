from eNMS import db
from eNMS.base.helpers import fetch_all


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


def object_import():
    if request.form.get('replace', None) == 'y':
        delete_all('Device')
    if request.form.get('update-pools', None) == 'y':
        for pool in fetch_all('Pool'):
            pool.compute_pool()
        db.session.commit()
    file, result = request.files['file'], 'Topology successfully imported.'
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
    return result