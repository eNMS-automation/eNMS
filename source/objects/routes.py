from base.database import db, get_obj
from base.helpers import allowed_file
from base.properties import (
    pretty_names,
    link_public_properties,
    node_public_properties
)
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from .forms import AddNode, AddLink, AddPoolForm, PoolObjectsForm
from .models import pool_factory, Pool, Link, Node, object_class, object_factory
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError

blueprint = Blueprint(
    'objects_blueprint',
    __name__,
    url_prefix='/objects',
    template_folder='templates',
    static_folder='static'
)

## Template rendering


@blueprint.route('/object_management', methods=['GET', 'POST'])
@login_required
def objects_management():
    add_node_form = AddNode(request.form)
    add_link_form = AddLink(request.form)
    all_nodes = Node.choices()
    add_link_form.source.choices = add_link_form.destination.choices = all_nodes
    if request.method == 'POST':
        file = request.files['file']
        if allowed_file(secure_filename(file.filename), {'xls', 'xlsx'}):
            book = open_workbook(file_contents=file.read())
            for obj_type, cls in object_class.items():
                try:
                    sheet = book.sheet_by_name(obj_type)
                # if the sheet cannot be found, there's nothing to import
                except XLRDError:
                    continue
                properties = sheet.row_values(0)
                for row_index in range(1, sheet.nrows):
                    kwargs = dict(zip(properties, sheet.row_values(row_index)))
                    kwargs['type'] = obj_type
                    object_factory(**kwargs)
                db.session.commit()
    return render_template(
        'object_management.html',
        names=pretty_names,
        node_fields=node_public_properties,
        nodes=Node.visible_objects(),
        link_fields=link_public_properties,
        links=Link.visible_objects(),
        add_node_form=add_node_form,
        add_link_form=add_link_form
    )


@blueprint.route('/pool_management')
@login_required
def pool_management():
    pool_object_form = PoolObjectsForm(request.form)
    pool_object_form.nodes.choices = Node.choices()
    pool_object_form.links.choices = Link.choices()
    return render_template(
        'pool_management.html',
        form=AddPoolForm(request.form),
        pool_object_form=pool_object_form,
        names=pretty_names,
        pools=Pool.query.all()
    )


## AJAX calls


@blueprint.route('/get/<obj_type>/<name>', methods=['POST'])
@login_required
def get_object(obj_type, name):
    cls = Node if obj_type == 'node' else Link
    properties = node_public_properties if cls == Node else link_public_properties
    obj = get_obj(cls, name=name)
    obj_properties = {
        property: str(getattr(obj, property))
        for property in properties
    }
    return jsonify(obj_properties)


@blueprint.route('/edit_object', methods=['GET', 'POST'])
@login_required
def edit_object():
    object_factory(**request.form.to_dict())
    db.session.commit()
    return jsonify({})


@blueprint.route('/delete/<obj_type>/<name>', methods=['POST'])
@login_required
def delete_object(obj_type, name):
    cls = Node if obj_type == 'node' else Link
    obj = get_obj(cls, name=name)
    db.session.delete(obj)
    db.session.commit()
    return jsonify({})


@blueprint.route('/process_pool', methods=['POST'])
@login_required
def process_pool():
    pool_properties = request.form.to_dict()
    for property in node_public_properties:
        regex_property = 'node_{}_regex'.format(property)
        pool_properties[regex_property] = regex_property in pool_properties
    for property in link_public_properties:
        regex_property = 'link_{}_regex'.format(property)
        pool_properties[regex_property] = regex_property in pool_properties
    pool_factory(**pool_properties)
    return jsonify()


@blueprint.route('/get_pool/<name>', methods=['POST'])
@login_required
def get_pool(name):
    return jsonify(get_obj(Pool, name=name).get_properties())


@blueprint.route('/get_pool_objects/<name>', methods=['POST'])
@login_required
def get_pool_objects(name):
    pool = get_obj(Pool, name=name)
    nodes = str(pool.nodes).replace(', ', ',')[1:-1].split(',')
    links = str(pool.links).replace(', ', ',')[1:-1].split(',')
    return jsonify({'nodes': nodes, 'links':links})


@blueprint.route('/save_pool_objects/<name>', methods=['POST'])
@login_required
def save_pool_objects(name):
    pool = get_obj(Pool, name=name)
    pool.nodes = [get_obj(Node, name=n) for n in request.form.getlist('nodes')]
    pool.links = [get_obj(Link, name=n) for n in request.form.getlist('links')]
    print(request.form)
    db.session.commit()
    return jsonify()


@blueprint.route('/pool_objects/<name>', methods=['POST'])
@login_required
def filter_pool_objects(name):
    pool = get_obj(Pool, name=name)
    objects = pool.filter_objects()
    return jsonify(objects)


@blueprint.route('/delete_pool/<name>', methods=['POST'])
@login_required
def delete_pool(name):
    pool = get_obj(Pool, name=name)
    db.session.delete(pool)
    db.session.commit()
    return jsonify({})
