from collections import Counter
from flask import jsonify, render_template, redirect, request, url_for

from eNMS.base import bp
from eNMS.base.models import classes
from eNMS.base.helpers import get, post
from eNMS.base.properties import (
    default_diagrams_properties,
    pretty_names,
    reverse_pretty_names,
    type_to_diagram_properties
)


@bp.route('/')
def site_root():
    return redirect(url_for('admin_blueprint.login'))


@get(bp, '/dashboard')
def dashboard():
    return render_template(
        'dashboard.html',
        names=pretty_names,
        properties=type_to_diagram_properties,
        default_properties=default_diagrams_properties,
        counters={name: len(cls.query.all()) for name, cls in classes.items()}
    )


@post(bp, '/counters/<property>/<type>')
def get_counters(property, type):
    objects = classes[type].query.all()
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return jsonify(Counter(map(lambda o: str(getattr(o, property)), objects)))


@post(bp, '/migration_export', 'Admin Section')
def migration_export():
    name = request.form['name']
    for cls_name in request.form.getlist('export'):
        path = app.path / 'migrations' / 'export' / name / f'{cls_name}.yaml'
        with open(path, 'w') as migration_file:
            instances = classes[cls_name].export()
            dump(instances, migration_file, default_flow_style=False)
    return jsonify(True)


@post(bp, '/migration_import', 'Admin Section')
def migration_import():
    name = request.form['name']
    for cls_name in request.form.getlist('export'):
        path = app.path / 'migrations' / 'export' / name / f'{cls_name}.yaml'
        with open(path, 'r') as migration_file:
            for obj_data in load(migration_file):
                obj = {}
                if cls_name == 'service':
                    cls = service_classes[obj_data.pop('type')]
                else:
                    cls = classes[cls_name]
                for property, value in obj_data.items():
                    if property not in import_properties[cls_name]:
                        continue
                    elif property in serialization_properties:
                        obj[property] = fetch(
                            classes[property]
                            if property not in ('source', 'destination')
                            else Device,
                            id=value
                        )
                    elif property[:-1] in serialization_properties:
                        obj[property] = objectify(classes[property[:-1]], value)
                    else:
                        obj[property] = value
                factory(cls, **obj)
    return jsonify(True)


@post(bp, '/shutdown', 'Admin')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'
