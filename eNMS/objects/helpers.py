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
