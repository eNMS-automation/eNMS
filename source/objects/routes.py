from base.database import db
from base.properties import pretty_names
from flask import Blueprint, current_app, render_template, request
from flask_login import login_required
from .forms import *
from .models import *
from objects.models import node_class, Node, Link
from os.path import join
from .properties import *
from re import search
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError

blueprint = Blueprint(
    'objects_blueprint', 
    __name__, 
    url_prefix = '/objects', 
    template_folder = 'templates',
    static_folder = 'static'
    )

def allowed_file(name, webpage):
    # allowed extensions depending on the webpage
    allowed_extensions = {'nodes': {'xls', 'xlsx'}, 'netmiko': {'yaml'}}
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions[webpage]
    return allowed_syntax and allowed_extension

@blueprint.route('/objects')
@login_required
def objects():
    links = Link.query.all()
    return render_template(
        'objects_overview.html',
        names = pretty_names,
        node_fields = node_public_properties, 
        nodes = Node.visible_objects(),
        link_fields = link_public_properties, 
        links = Link.visible_objects()
        )

@blueprint.route('/object_creation', methods=['GET', 'POST'])
@login_required
def create_objects():
    add_node_form = AddNode(request.form)
    add_nodes_form = AddNodes(request.form)
    add_link_form = AddLink(request.form)
    if 'add_node' in request.form:
        node = node_class[request.form['type']](**request.form)
        db.session.add(node)
        db.session.commit()
    elif 'add_nodes' in request.form:
        filename = request.files['file'].filename
        if 'file' in request.files and allowed_file(filename, 'nodes'):  
            filename = secure_filename(filename)
            filepath = join(current_app.config['UPLOAD_FOLDER'], filename)
            request.files['file'].save(filepath)
            book = open_workbook(filepath)
            for obj_type, cls in object_class.items():
                try:
                    sheet = book.sheet_by_name(obj_type)
                # if the sheet cannot be found, there's nothing to import
                except XLRDError:
                    continue
                print(obj_type, sheet.row_values(0))
                properties = sheet.row_values(0)
                for row_index in range(1, sheet.nrows):
                    kwargs = dict(zip(properties, sheet.row_values(row_index)))
                    if obj_type in link_class:
                        source = db.session.query(Node)\
                            .filter_by(name=kwargs.pop('source'))\
                            .first()
                        destination = db.session.query(Node)\
                            .filter_by(name=kwargs.pop('destination'))\
                            .first()
                        new_obj = link_class[obj_type](
                            source_id = source.id, 
                            destination_id = destination.id, 
                            source = source, 
                            destination = destination,
                            **kwargs
                            )
                    else:
                        new_obj = node_class[obj_type](**kwargs)
                    db.session.add(new_obj)
                db.session.commit()
        else:
            flash('no file submitted')
    elif 'add_link' in request.form:
        source = db.session.query(Node)\
            .filter_by(name=request.form['source'])\
            .first()
        destination = db.session.query(Node)\
            .filter_by(name=request.form['destination'])\
            .first()
        new_link = EthernetLink(
            source_id = source.id, 
            destination_id = destination.id, 
            source = source, 
            destination = destination
            )
        db.session.add(new_link)
        db.session.commit()
    all_nodes = Node.choices()
    add_link_form.source.choices = add_link_form.destination.choices = all_nodes
    return render_template(
        'create_object.html',
        add_node_form = add_node_form,
        add_nodes_form = add_nodes_form,
        add_link_form = add_link_form
        )

@blueprint.route('/object_deletion', methods=['GET', 'POST'])
@login_required
def delete_objects():
    delete_objects_form = DeleteObjects(request.form)
    if request.method == 'POST':
        # delete nodes
        node_selection = delete_objects_form.data['nodes']
        db.session.query(Object).filter(Object.name.in_(node_selection))\
        .delete(synchronize_session='fetch')
        # delete links
        link_selection = delete_objects_form.data['links']
        db.session.query(Object).filter(Object.name.in_(link_selection))\
        .delete(synchronize_session='fetch')
        db.session.commit()
    delete_objects_form.nodes.choices = Node.visible_choices()
    delete_objects_form.links.choices = Link.visible_choices()
    return render_template(
        'object_deletion.html',
        form = delete_objects_form
        )

@blueprint.route('/object_filtering', methods=['GET', 'POST'])
@login_required
def filter_objects():
    form = FilteringForm(request.form)
    if request.method == 'POST':
        # value = 
        print(request.form)
        for obj in Node.query.all() + Link.query.all():
            print(obj.__dict__, request.form)
            # source and destination do not belong to a link __dict__, because
            # they are SQLalchemy relationships and not columns
            # we update __dict__ with these properties for the filtering
            # system to work
            if obj.class_type == 'link':
                obj.__dict__.update({
                    'source': obj.source,
                    'destination': obj.destination
                    })
            obj.visible = all(
                # if the node-regex property is not in the request, the
                # regex box is unticked and we only check that the values
                # are equal.
                str(value) == request.form[obj.class_type + property]
                if not obj.class_type + property + 'regex' in request.form
                # if it is ticked, we use re.search to check that the value
                # of the node property matches the regular expression.
                else search(request.form[obj.class_type + property], str(value))
                for property, value in obj.__dict__.items()
                # we consider only the properties in the form 
                if obj.class_type + property in request.form
                # providing that the property field in the form is not empty
                # (empty field <==> property ignored)
                and request.form[obj.class_type + property]
                )
    # the visible status was updated, we need to commit the change
    db.session.commit()
    return render_template(
        'object_filtering.html',
        form = form,
        names = pretty_names
        )