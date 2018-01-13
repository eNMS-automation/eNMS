from base.database import db
from base.properties import pretty_names
from collections import OrderedDict
from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from flask_login import current_user, login_required
from .forms import *
from functools import partial
from objects.models import *
from objects.properties import *
from os.path import join
# from simplekml import Color, Kml, Style
from subprocess import Popen

blueprint = Blueprint(
    'views_blueprint', 
    __name__, 
    url_prefix = '/views', 
    template_folder = 'templates',
    static_folder = 'static'
    )

styles = {}

@blueprint.route('/<view_type>_view', methods = ['GET', 'POST'])
@login_required
def view(view_type):
    view_options_form = ViewOptionsForm(request.form)
    google_earth_form = GoogleEarthForm(request.form)
    labels = {'node': 'name', 'link': 'name'}
    if 'view_options' in request.form:
        # retrieve labels
        labels = {
            'node': request.form['node_label'],
            'link': request.form['link_label']
            }
    elif 'google_earth' in request.form:
        kml_file = Kml()
        
        for node in filter(lambda obj: obj.visible, Node.query.all()):
            point = kml_file.newpoint(name=node.name)
            point.coords = [(node.longitude, node.latitude)]
            point.style = styles[node.subtype]
            point.style.labelstyle.scale = request.form['label_size']
            
        for link in filter(lambda obj: obj.visible, Link.query.all()):
            line = kml_file.newlinestring(name=link.name) 
            line.coords = [
                (link.source.longitude, link.source.latitude),
                (link.destination.longitude, link.destination.latitude)
                ]
            line.style = styles[link.type]
            line.style.linestyle.width = request.form['line_width']
        
        filepath = join(current_app.kmz_path, request.form['name'] + '.kmz')
        kml_file.save(filepath)
        
    return render_template(
        '{}_view.html'.format(view_type), 
        view_options_form = view_options_form,
        google_earth_form = google_earth_form,
        labels = labels,
        names = pretty_names,
        subtypes = node_subtypes,
        node_table = {
            obj: OrderedDict([
                (property, getattr(obj, property)) 
                for property in type_to_public_properties[obj.type]
            ])
            for obj in filter(lambda obj: obj.visible, Node.query.all())
        },
        link_table = {
            obj: OrderedDict([
                (property, getattr(obj, property)) 
                for property in type_to_public_properties[obj.type]
            ])
            for obj in filter(lambda obj: obj.visible, Link.query.all())
        })

@blueprint.route('/putty_connection', methods = ['POST'])
@login_required
def putty_connection():
    print(request.form)
    node = db.session.query(Node)\
        .filter_by(id=request.form['id'])\
        .first()
    path_putty = join(current_app.path_apps, 'putty.exe')
    ssh_connection = '{} -ssh {}@{} -pw {}'.format(
        path_putty,
        current_user.username,
        node.ip_address,
        current_user.password
        )
    connect = Popen(ssh_connection.split())
    return jsonify(id=request.form['id'])
