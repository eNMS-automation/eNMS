from base.database import db
from base.routes import _render_template
from flask import Blueprint, current_app, request
from flask_login import login_required
from .forms import *
from .models import *
from objects.models import node_class
from os.path import join
from .properties import *
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError

blueprint = Blueprint(
    'objects_blueprint', 
    __name__, 
    url_prefix = '/objects', 
    template_folder = 'templates'
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
    return _render_template(
        'objects_overview.html', 
        node_fields = node_public_properties, 
        nodes = Node.query.all(),
        link_fields = link_public_properties, 
        links = Link.query.all()
        )

@blueprint.route('/object_creation', methods=['GET', 'POST'])
@login_required
def create_objects():
    add_node_form = AddNode(request.form)
    add_nodes_form = AddNodes(request.form)
    add_link_form = AddLink(request.form)
    if 'add_node' in request.form:
        # print(request.form, request.form['type'])
        node = node_class[request.form['type']](**request.form)
        db.session.add(node)
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
    if request.method == 'POST':
        db.session.commit()
    all_nodes = Node.choices()
    add_link_form.source.choices = add_link_form.destination.choices = all_nodes
    return _render_template(
        'create_object.html',
        add_node_form = add_node_form,
        add_nodes_form = add_nodes_form,
        add_link_form = add_link_form
        )
