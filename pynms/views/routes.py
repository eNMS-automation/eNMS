from base.routes import _render_template
from flask import Blueprint, request
from flask_login import login_required
from objects.models import Node, Link

blueprint = Blueprint(
    'views_blueprint', 
    __name__, 
    url_prefix = '/views', 
    template_folder = 'templates',
    static_folder='static'
    )

@blueprint.route('/geographical_view')
@login_required
def geographical_view():
    node_fields = tuple(Node.__table__.columns._data)
    nodes = Node.query.all()
    node_table = {}
    for node in nodes:
        lines = {field: getattr(node, field) for field in node_fields}
        node_table[node] = lines
    link_fields = tuple(Link.__table__.columns._data)
    links = Link.query.all()
    link_table = {}
    for link in links:
        lines = {field: getattr(link, field) for field in link_fields}
        link_table[link] = lines
    return _render_template(
        'geographical_view.html', 
        node_table = node_table,
        link_table = link_table
        )
                           
@blueprint.route('/logical_view')
@login_required
def logical_view():
    node_fields = tuple(Node.__table__.columns._data)
    nodes = Node.query.all()
    node_table = {}
    for node in nodes:
        lines = {field: getattr(node, field) for field in node_fields}
        node_table[node] = lines
    link_fields = tuple(Link.__table__.columns._data)
    links = Link.query.all()
    link_table = {}
    for link in links:
        lines = {field: getattr(link, field) for field in link_fields}
        link_table[link] = lines
    return _render_template(
        'logical_view.html', 
        node_table = node_table,
        link_table = link_table
        )

@blueprint.route('/ajax_connection_to_node2', methods = ['POST'])
@login_required
def ajax_request2():
    id = request.form['id']
    print(id)
    return jsonify(id=id)

@blueprint.route('/ajax_connection_to_node', methods = ['POST'])
@login_required
def ajax_request():
    ip_address = request.form['ip_address']
    path_putty = join(APPS_FOLDER, 'putty.exe')
    ssh_connection = '{} -ssh {}'.format(path_putty, ip_address)
    connect = Popen(ssh_connection.split())
    return jsonify(ip_address=ip_address)