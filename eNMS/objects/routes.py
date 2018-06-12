from flask import jsonify, render_template, request
from flask_login import login_required
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError


from eNMS import db
from eNMS.base.helpers import allowed_file, get_obj
from eNMS.objects import blueprint
from eNMS.objects.forms import AddLink, AddNode, AddPoolForm, PoolObjectsForm
from eNMS.objects.models import (
    Link,
    Node,
    object_class,
    object_factory,
    Pool,
    pool_factory
)
from eNMS.base.properties import (
    link_public_properties,
    node_public_properties,
    pool_public_properties,
    pretty_names
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
        nodes=Node.serialize(),
        link_fields=link_public_properties,
        links=Link.serialize(),
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
        fields=pool_public_properties,
        pools=Pool.serialize()
    )


## AJAX calls


@blueprint.route('/get/<obj_type>/<obj_id>', methods=['POST'])
@login_required
def get_object(obj_type, obj_id):
    cls = Node if obj_type == 'node' else Link
    properties = node_public_properties if cls == Node else link_public_properties
    print(obj_type, obj_id)
    obj = get_obj(cls, id=obj_id)
    obj_properties = {
        property: str(getattr(obj, property))
        for property in properties
    }
    return jsonify(obj_properties)


@blueprint.route('/edit_object', methods=['POST'])
@login_required
def edit_object():
    obj = object_factory(**request.form.to_dict())
    return jsonify(obj.serialized)


@blueprint.route('/delete/<obj_type>/<obj_id>', methods=['POST'])
@login_required
def delete_object(obj_type, obj_id):
    cls = Node if obj_type == 'node' else Link
    obj = get_obj(cls, id=obj_id)
    db.session.delete(obj)
    db.session.commit()
    return jsonify({'name': obj.name})


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
    pool = pool_factory(**pool_properties)
    return jsonify(pool.serialized)


@blueprint.route('/get_pool/<pool_id>', methods=['POST'])
@login_required
def get_pool(pool_id):
    return jsonify(get_obj(Pool, id=pool_id).get_properties())


@blueprint.route('/get_pool_objects/<pool_id>', methods=['POST'])
@login_required
def get_pool_objects(pool_id):
    pool = get_obj(Pool, id=pool_id)
    print(pool.serialized)
    return jsonify(pool.serialized)


@blueprint.route('/save_pool_objects/<pool_id>', methods=['POST'])
@login_required
def save_pool_objects(pool_id):
    pool = get_obj(Pool, id=pool_id)
    pool.nodes = [get_obj(Node, id=id) for id in request.form.getlist('nodes')]
    pool.links = [get_obj(Link, id=id) for id in request.form.getlist('links')]
    db.session.commit()
    return jsonify(pool.name)


@blueprint.route('/pool_objects/<pool_id>', methods=['POST'])
@login_required
def filter_pool_objects(pool_id):
    pool = get_obj(Pool, id=pool_id)
    return jsonify(pool.filter_objects())


@blueprint.route('/update_pools', methods=['POST'])
@login_required
def update_pools():
    for pool in Pool.query.all():
        pool.compute_pool()
    db.session.commit()
    return jsonify({})


@blueprint.route('/delete_pool/<pool_id>', methods=['POST'])
@login_required
def delete_pool(pool_id):
    pool = get_obj(Pool, id=pool_id)
    db.session.delete(pool)
    db.session.commit()
    return jsonify(pool.name)
