from base.database import db
from base.routes import _render_template
from collections import OrderedDict
from flask import Blueprint, current_app, jsonify, request, send_file
from flask_login import login_required
from .forms import *
from functools import partial
from main import path_source
from objects.models import *
from objects.properties import *
from os.path import join
from re import search
from simplekml import Color, Kml, Style
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
    labels = {'node': 'name', 'link': 'name'}
    if request.method == 'POST':
        # retrieve labels
        labels = {
            'node': request.form['node_label'],
            'link': request.form['link_label']
            }
        for obj in Node.query.all() + Link.query.all():
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
            # we consider only public properties
            if property in obj.get_properties()
            # providing that the property field in the form is not empty
            # (empty field <==> property ignored)
            and request.form[obj.class_type + property]
            )
    # the visible status was updated, we need to commit the change
    db.session.commit()
    return _render_template(
        '{}_view.html'.format(view_type), 
        form = FilteringForm(request.form),
        labels = labels,
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
    node = db.session.query(Node)\
        .filter_by(id=request.form['id'])\
        .first()
    path_putty = join(current_app.path_apps, 'putty.exe')
    ssh_connection = '{} -ssh {}'.format(path_putty, node.ip_address)
    connect = Popen(ssh_connection.split())
    return jsonify(id=request.form['id'])

## Export to Google Earth

styles = {}
for subtype in node_class:
    point_style = Style()
    point_style.labelstyle.color = Color.blue
    path_icon = join(path_source, 'views', 'static', 'images', 'default', '{}.gif'.format(subtype))
    point_style.iconstyle.icon.href = path_icon
    styles[subtype] = point_style
    
for subtype, cls in link_class.items():
    line_style = Style()
    # we convert the RGB color to a KML color, 
    # i.e #RRGGBB to #AABBGGRR
    kml_color = "#ff" + cls.color[-2:] + cls.color[2:4] + cls.color[:2]
    line_style.linestyle.color = kml_color
    styles[subtype] = line_style

@blueprint.route('/export', methods = ['POST'])
@login_required
def export():
    kml_file = Kml()
    
    for node in filter(lambda obj: obj.visible, Node.query.all()):
        point = kml_file.newpoint(name=node.name)
        point.coords = [(node.longitude, node.latitude)]
        point.style = styles[node.type]
        point.style.labelstyle.scale = 2
        
    for link in filter(lambda obj: obj.visible, Link.query.all()):
        line = kml_file.newlinestring(name=link.name) 
        line.coords = [(link.source.longitude, link.source.latitude),
                    (link.destination.longitude, link.destination.latitude)]
        line.style = styles[link.type]
        line.style.linestyle.width = 2
    
    filepath = join(current_app.kmz_path, 'test.kmz')
    kml_file.save(filepath)
    return jsonify(id=request.form['id'])