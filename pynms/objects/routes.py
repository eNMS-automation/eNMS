from base.routes import _render_template
from flask import Blueprint, current_app, request
from flask_login import login_required
from os.path import join
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from .models import *
from .forms import *

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
        node_fields = Node.get_properties(), 
        nodes = Node.query.all(),
        link_fields = Link.get_properties(), 
        links = Link.query.all()
        )

@blueprint.route('/object_creation', methods=['GET', 'POST'])
@login_required
def create_objects():
    add_node_form = AddNode(request.form)
    add_nodes_form = AddNodes(request.form)
    add_link_form = AddLink(request.form)
    if 'add_node' in request.form:
        node = Node(**request.form)
        current_app.database.session.add(node)
    elif 'add_nodes' in request.form:
        filename = request.files['file'].filename
        if 'file' in request.files and allowed_file(filename, 'nodes'):  
            filename = secure_filename(filename)
            filepath = join(current_app.config['UPLOAD_FOLDER'], filename)
            request.files['file'].save(filepath)
            book = open_workbook(filepath)
            sheet = book.sheet_by_index(0)
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                kwargs = dict(zip(properties, sheet.row_values(row_index)))
                node_type = kwargs.pop('type')
                new_node = node_class[node_type](**kwargs)
                current_app.database.session.add(new_node)
        else:
            flash('no file submitted')
    elif 'add_link' in request.form:
        source = current_app.database.session.query(Node)\
            .filter_by(name=request.form['source'])\
            .first()
        destination = current_app.database.session.query(Node)\
            .filter_by(name=request.form['destination'])\
            .first()
        new_link = EthernetLink(
            source_id = source.id, 
            destination_id = destination.id, 
            source = source, 
            destination = destination
            )
        current_app.database.session.add(new_link)
    if request.method == 'POST':
        current_app.database.session.commit()
    all_nodes = Node.choices()
    add_link_form.source.choices = add_link_form.destination.choices = all_nodes
    return _render_template(
        'create_object.html',
        add_node_form = add_node_form,
        add_nodes_form = add_nodes_form,
        add_link_form = add_link_form
        )
