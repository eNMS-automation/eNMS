from os import makedirs
from os.path import exists
from yaml import dump, load


def migrate(path_app, request):
    for cls_name in request['import_export_types']:
        path = path_app / 'migrations' / request['name']
        if not exists(path):
            makedirs(path)
        with open(path / f'{cls_name}.yaml', 'w') as migration_file:
            dump(export(cls_name), migration_file, default_flow_style=False)
    return True