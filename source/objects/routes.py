from base.database import db
from base.helpers import allowed_file
from base.properties import pretty_names
from flask import Blueprint, current_app, render_template, request
from flask_login import login_required
from .forms import *
from .models import *
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
        object_factory(db, Node, **request.form.to_dict())
    elif 'add_nodes' in request.form:
        filename = request.files['file'].filename
        if 'file' in request.files and allowed_file(filename, {'xls', 'xlsx'}):  
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
                properties = sheet.row_values(0)
                for row_index in range(1, sheet.nrows):
                    kwargs = dict(zip(properties, sheet.row_values(row_index)))
                    if obj_type in link_class:
                        source = get_obj(db, Node, name=kwargs.pop('source'))
                        destination = get_obj(db, Node, name=kwargs.pop('destination'))
                        new_link = link_class[obj_type](
                            source_id = source.id, 
                            destination_id = destination.id, 
                            source = source, 
                            destination = destination,
                            **kwargs
                            )
                        db.session.add(new_link)
                    else:
                        kwargs['type'] = obj_type
                        object_factory(db, Node, **kwargs)
                db.session.commit()
        else:
            flash('no file submitted')
    elif 'add_link' in request.form:
        link_form = request.form.to_dict()
        form_source = link_form.pop('source')
        source = db.session.query(Node)\
            .filter_by(name=form_source)\
            .first()
        form_destination = link_form.pop('destination')
        destination = db.session.query(Node)\
            .filter_by(name=form_destination)\
            .first()
        new_link = EthernetLink(
            source_id = source.id, 
            destination_id = destination.id, 
            source = source, 
            destination = destination,
            **link_form
            )
        db.session.add(new_link)
        db.session.commit()
    all_nodes = Node.visible_choices()
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
        for node in node_selection:
            node = db.session.query(Object).filter_by(name=node).first()
            db.session.delete(node)
        # note: a Query.delete() bypasses cascade deletes: we musn't do it
        # db.session.query(Object).filter(Object.name.in_(node_selection))\
        # .delete(synchronize_session='fetch')
        # delete links
        link_selection = delete_objects_form.data['links']
        for link in link_selection:
            print(link)
            link = db.session.query(Object).filter_by(name=link).first()
            db.session.delete(link)
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
        for obj in Node.query.all() + Link.query.all():
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