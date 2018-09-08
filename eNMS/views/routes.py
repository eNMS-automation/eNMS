from flask import current_app, jsonify, render_template, request
from flask_login import login_required
from os import system as os_system
from os.path import join
from platform import system as platform_system
from simplekml import Kml
from subprocess import Popen

from eNMS.admin.models import Parameters
from eNMS.base.helpers import get_credentials, retrieve
from eNMS.base.properties import device_subtypes, link_subtype_to_color
from eNMS.base.models import Log
from eNMS.objects.forms import AddDevice, AddLink
from eNMS.objects.models import Pool, Device, Link
from eNMS.base.properties import (
    link_public_properties,
    device_public_properties,
    pretty_names
)
from eNMS.scripts.models import Job
from eNMS.tasks.forms import SchedulingForm
from eNMS.views import blueprint, styles
from eNMS.views.forms import GoogleEarthForm, ViewOptionsForm


@blueprint.route('/<view_type>_view', methods=['GET', 'POST'])
@login_required
def view(view_type):
    add_device_form = AddDevice(request.form)
    add_link_form = AddLink(request.form)
    all_devices = Device.choices()
    add_link_form.source.choices = all_devices
    add_link_form.destination.choices = all_devices
    view_options_form = ViewOptionsForm(request.form)
    google_earth_form = GoogleEarthForm(request.form)
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    scheduling_form.devices.choices = all_devices
    scheduling_form.pools.choices = Pool.choices()
    labels = {'device': 'name', 'link': 'name'}
    if 'view_options' in request.form:
        # update labels
        labels = {
            'device': request.form['device_label'],
            'link': request.form['link_label']
        }
    # for the sake of better performances, the view defaults to markercluster
    # if there are more than 2000 devices
    view = 'leaflet' if len(Device.query.all()) < 2000 else 'markercluster'
    if 'view' in request.form:
        view = request.form['view']
    # name to id
    name_to_id = {
        device.name: id for id, device in enumerate(Device.query.all())
    }
    return render_template(
        f'{view_type}_view.html',
        pools=Pool.query.all(),
        parameters=Parameters.query.one().serialized,
        view=view,
        scheduling_form=scheduling_form,
        view_options_form=view_options_form,
        google_earth_form=google_earth_form,
        add_device_form=add_device_form,
        add_link_form=add_link_form,
        device_fields=device_public_properties,
        link_fields=link_public_properties,
        labels=labels,
        names=pretty_names,
        device_subtypes=device_subtypes,
        link_colors=link_subtype_to_color,
        name_to_id=name_to_id,
        devices=Device.serialize(),
        links=Link.serialize()
    )


@blueprint.route('/connect_to_<name>', methods=['POST'])
@login_required
def putty_connection(name):
    current_os, device = platform_system(), retrieve(Device, name=name)
    username, password, _ = get_credentials(device)
    if current_os == 'Windows':
        path_putty = join(current_app.path, 'applications', 'putty.exe')
        ssh = f'{path_putty} -ssh {username}@{device.ip_address} -pw {password}'
        Popen(ssh.split())
    else:
        sshpass = f'"sshpass -p {password} ssh {username}@{device.ip_address}"'
        os_system(f'gnome-terminal -- /bin/bash -c {sshpass}')
    return jsonify({'success': True})


@blueprint.route('/export_to_google_earth', methods=['POST'])
@login_required
def export_to_google_earth():
    kml_file = Kml()
    for device in Device.query.all():
        point = kml_file.newpoint(name=device.name)
        point.coords = [(device.longitude, device.latitude)]
        point.style = styles[device.subtype]
        point.style.labelstyle.scale = request.form['label_size']
    for link in Link.query.all():
        line = kml_file.newlinestring(name=link.name)
        line.coords = [
            (link.source.longitude, link.source.latitude),
            (link.destination.longitude, link.destination.latitude)
        ]
        line.style = styles[link.type]
        line.style.linestyle.width = request.form['line_width']
    filepath = join(
        current_app.path,
        'google_earth',
        f'{request.form["name"]}.kmz'
    )
    kml_file.save(filepath)
    return jsonify({'success': True})


@blueprint.route('/get_logs_<device_id>', methods=['POST'])
@login_required
def get_logs(device_id):
    device = retrieve(Device, id=device_id)
    device_logs = [
        l.content for l in Log.query.all()
        if l.source == device.ip_address
    ]
    return jsonify('\n'.join(device_logs))
