from base.routes import _render_template
from flask import Blueprint, request
from flask_login import login_required
from .forms import *
from objects.models import Node, Link
from objects.properties import *

blueprint = Blueprint(
    'views_blueprint', 
    __name__, 
    url_prefix = '/views', 
    template_folder = 'templates',
    static_folder='static'
    )

@blueprint.route('/<view_type>_view', methods = ['GET', 'POST'])
@login_required
def view(view_type):
    view_filter = lambda _: True
    if request.method == 'POST':
        def view_filter(obj):
            if obj.class_type == 'node':
                return all(
                    str(value) == request.form['node' + property]
                    for property, value in obj.__dict__.items()
                    if property in node_public_properties 
                    and request.form['node' + property]
                    )
            elif obj.class_type == 'link':
                return all(
                    str(value) == request.form['link' + property]
                    for property, value in obj.__dict__.items()
                    if property in link_public_properties
                    and request.form['link' + property]
                    )
    return _render_template(
        '{}_view.html'.format(view_type), 
        form = FilteringForm(request.form),
        node_table = {
            obj: {
                property: getattr(obj, property) 
                for property in type_to_public_properties[obj.type]
            }
            for obj in filter(view_filter, Node.query.all())
        },
        link_table = {
            obj: {
                property: getattr(obj, property) 
                for property in type_to_public_properties[obj.type]
            }
            for obj in filter(view_filter, Link.query.all())
        })

@blueprint.route('/ajax_connection_to_node2', methods = ['POST'])
@login_required
def ajax_request2():
    id = request.form['id']
    print(id)
    return jsonify(id=id)

@blueprint.route('/ajax_connection_to_node', methods = ['POST'])
@login_required
def ajax_request():
    print(t*100000)
    ip_address = request.form['ip_address']
    path_putty = join(APPS_FOLDER, 'putty.exe')
    ssh_connection = '{} -ssh {}'.format(path_putty, ip_address)
    connect = Popen(ssh_connection.split())
    return jsonify(ip_address=ip_address)