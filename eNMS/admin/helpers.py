from datetime import datetime
from logging import info
from os import makedirs
from os.path import exists
from yaml import dump, load

from eNMS.base.helpers import delete_all, export, factory, get_one


def configure_instance_id():
    parameters = get_one('Parameters')
    if not parameters.instance_id:
        now = str(datetime.now())
        parameters.instance_id = now
        factory('Instance', **{
            'name': now,
            'ip_address': '0.0.0.0',
            'status': 'Up'
        })


def migrate_export(path_app, request):
    for cls_name in request['import_export_types']:
        path = path_app / 'migrations' / request['name']
        if not exists(path):
            makedirs(path)
        with open(path / f'{cls_name}.yaml', 'w') as migration_file:
            dump(export(cls_name), migration_file, default_flow_style=False)
    return True


def migrate_import(path_app, request):
    status = 'Import successful.'
    if request.get('empty_database_before_import', False):
        delete_all(*request['import_export_types'])
    for cls in request['import_export_types']:
        path = path_app / 'migrations' / request['name'] / f'{cls}.yaml'
        with open(path, 'r') as migration_file:
            for obj in load(migration_file):
                obj_cls = obj.pop('type') if cls == 'Service' else cls
                try:
                    factory(obj_cls, **obj)
                except Exception as e:
                    info(f'{str(obj)} could not be imported ({str(e)})')
                    status = 'Partial import (see logs).'
    return status
