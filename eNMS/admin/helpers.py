from os import makedirs
from os.path import exists
from yaml import dump, load


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
    if request.form['empty_database_before_import']:
        delete_all(*request.form['import_export_types'])
    for cls in request.form['import_export_types']:
        path = app.path / 'migrations' / request.form['name'] / f'{cls}.yaml'
        with open(path, 'r') as migration_file:
            for obj in load(migration_file):
                try:
                    factory(obj.pop('type') if cls == 'Service' else cls, **obj)
                except Exception as e:
                    info(f'{str(obj)} could not be imported ({str(e)})')
                    status = 'Partial import (see logs).'
    return status