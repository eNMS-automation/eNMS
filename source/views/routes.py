from base.database import db
from base.properties import pretty_names
from collections import OrderedDict
from flask import Blueprint, current_app, render_template, redirect, request, session, url_for
from flask_login import current_user, login_required
from .forms import GoogleEarthForm, SchedulingForm, ViewOptionsForm
from json import dumps
from objects.models import get_obj, Node, node_subtypes, Link, link_class
from objects.properties import type_to_public_properties
from os.path import join
from scripts.models import Script
from simplekml import Color, Kml, Style
from subprocess import Popen
from tasks.models import Task

blueprint = Blueprint(
    'views_blueprint',
    __name__,
    url_prefix='/views',
    template_folder='templates',
    static_folder='static'
)

styles = {}

for subtype in node_subtypes:
    point_style = Style()
    point_style.labelstyle.color = Color.blue
    path_icon = join(
        blueprint.root_path,
        'static',
        'images',
        'default',
        '{}.gif'.format(subtype)
    )
    point_style.iconstyle.icon.href = path_icon
    styles[subtype] = point_style

for subtype, cls in link_class.items():
    line_style = Style()
    # we convert the RGB color to a KML color,
    # i.e #RRGGBB to #AABBGGRR
    kml_color = "#ff" + cls.color[-2:] + cls.color[3:5] + cls.color[1:3]
    line_style.linestyle.color = kml_color
    styles[subtype] = line_style


@blueprint.route('/<view_type>_view', methods=['GET', 'POST'])
@login_required
def view(view_type):
    view_options_form = ViewOptionsForm(request.form)
    google_earth_form = GoogleEarthForm(request.form)
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.scripts.choices = Script.choices()
    labels = {'node': 'name', 'link': 'name'}
    if 'script' in request.form:
        data = dict(request.form)
        selection = map(int, session['selection'])
        scripts = request.form.getlist('scripts')
        data['scripts'] = [get_obj(db, Script, name=name) for name in scripts]
        data['nodes'] = [get_obj(db, Node, id=id) for id in selection]
        data['user'] = current_user
        task = Task(**data)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('tasks_blueprint.task_management'))
    elif 'view_options' in request.form:
        # update labels
        labels = {
            'node': request.form['node_label'],
            'link': request.form['link_label']
        }
    # for the sake of better performances, the view defaults to markercluster
    # if there are more than 2000 nodes
    view = 'leaflet' if len(Node.query.all()) < 2000 else 'markercluster'
    if 'view' in request.form:
        view = request.form['view']
    # we clean the session's selected nodes
    session['selection'] = []
    return render_template(
        '{}_view.html'.format(view_type),
        view=view,
        scheduling_form=scheduling_form,
        view_options_form=view_options_form,
        google_earth_form=google_earth_form,
        labels=labels,
        names=pretty_names,
        subtypes=node_subtypes,
        node_table={
            obj: OrderedDict([
                (property, getattr(obj, property))
                for property in type_to_public_properties[obj.type]
            ])
            for obj in filter(lambda obj: obj.visible, Node.query.all())
        },
        link_table={
            obj: OrderedDict([
                (property, getattr(obj, property))
                for property in type_to_public_properties[obj.type]
            ])
            for obj in filter(lambda obj: obj.visible, Link.query.all())
        })


@blueprint.route('/google_earth_export', methods=['GET', 'POST'])
@login_required
def google_earth_export():
    form = GoogleEarthForm(request.form)
    if 'POST' in request.method:
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
        filepath = join(current_app.ge_path, request.form['name'] + '.kmz')
        kml_file.save(filepath)
    return render_template(
        'google_earth_export.html',
        form=form
    )


@blueprint.route('/putty_connection', methods=['POST'])
@login_required
def putty_connection():
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
    Popen(ssh_connection.split())
    return dumps({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route('/selection', methods=['POST'])
@login_required
def selection():
    session['selection'] = list(set(request.form.getlist('selection[]')))
    print(session['selection'])
    return dumps({'success': True}), 200, {'ContentType': 'application/json'}
