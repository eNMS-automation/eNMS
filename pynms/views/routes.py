from base.routes import _render_template
from collections import OrderedDict
from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required
from .forms import *
from objects.models import Node, Link
from objects.properties import *
from os.path import join
from re import search
from subprocess import Popen

blueprint = Blueprint(
    'views_blueprint', 
    __name__, 
    url_prefix = '/views', 
    template_folder = 'templates',
    static_folder = 'static'
    )

@blueprint.route('/<view_type>_view', methods = ['GET', 'POST'])
@login_required
def view(view_type):
    view_filter = lambda _: True
    labels = {'node': 'name', 'link': 'name'}
    if request.method == 'POST':
        # retrieve labels
        labels = {
            'node': request.form['node_label'],
            'link': request.form['link_label']
            }
        def view_filter(obj):
            # if the property field is not empty in the form, and the 
            # property is a public property, we check that the value of 
            # the object matches the user input for all properties
            return all(
                # if the node-regex property is not in the request, the
                # regex box is unticked and we only check that the values
                # are equal.
                str(value) == request.form[obj.class_type + property]
                if not obj.class_type + property + 'regex' in request.form
                # if it is ticked, we use re.search to check that the value
                # of the node property matches the regular expression.
                else search(request.form[obj.class_type + property], str(value))
                for property, value in obj.__dict__.items()
                # we consider only public properties
                if property in obj.get_properties()
                # providing that the property field in the form is not empty
                # (empty field <==> property ignored)
                and request.form[obj.class_type + property]
                )
    return _render_template(
        '{}_view.html'.format(view_type), 
        form = FilteringForm(request.form),
        labels = labels,
        node_table = {
            obj: OrderedDict([
                (property, getattr(obj, property)) 
                for property in type_to_public_properties[obj.type]
            ])
            for obj in filter(view_filter, Node.query.all())
        },
        link_table = {
            obj: OrderedDict([
                (property, getattr(obj, property)) 
                for property in type_to_public_properties[obj.type]
            ])
            for obj in filter(view_filter, Link.query.all())
        })

@blueprint.route('/putty_connection', methods = ['POST'])
@login_required
def putty_connection():
    node = current_app.database.session.query(Node)\
        .filter_by(id=request.form['id'])\
        .first()
    path_putty = join(current_app.path_apps, 'putty.exe')
    ssh_connection = '{} -ssh {}'.format(path_putty, node.ip_address)
    connect = Popen(ssh_connection.split())
    return jsonify(id=request.form['id'])