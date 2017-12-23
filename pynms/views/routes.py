from base.routes import _render_template
from flask import Blueprint, request
from flask_login import login_required
from objects.models import Object
from objects.properties import *

blueprint = Blueprint(
    'views_blueprint', 
    __name__, 
    url_prefix = '/views', 
    template_folder = 'templates',
    static_folder='static'
    )

@blueprint.route('/<view_type>_view')
@login_required
def geographical_view(view_type):
    return _render_template(
        '{}_view.html'.format(view_type), 
        table = {
            obj: {
                property: getattr(obj, property) 
                for property in type_to_public_properties[obj.type]
            }
            for obj in Object.query.all()
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