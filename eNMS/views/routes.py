from flask import current_app, jsonify, render_template, request
from flask_login import login_required
from os.path import join
from simplekml import Kml

from eNMS.admin.models import Parameters
from eNMS.base.helpers import permission_required, retrieve
from eNMS.base.models import Log
from eNMS.base.properties import device_subtypes, link_subtype_to_color
from eNMS.objects.forms import AddDevice, AddLink
from eNMS.objects.models import Pool, Device, Link
from eNMS.base.properties import (
    link_public_properties,
    device_public_properties,
    pretty_names
)
from eNMS.services.models import Job
from eNMS.tasks.forms import SchedulingForm
from eNMS.views import blueprint, styles
from eNMS.views.forms import GoogleEarthForm, ViewOptionsForm


@blueprint.route('/<view_type>_view', methods=['GET', 'POST'])
@login_required
@permission_required('Views section')
def view(view_type):
    add_link_form = AddLink(request.form)
    all_devices = Device.choices()
    add_link_form.source.choices = all_devices
    add_link_form.destination.choices = all_devices
    scheduling_form = SchedulingForm(request.form)
    scheduling_form.job.choices = Job.choices()
    scheduling_form.devices.choices = all_devices
    scheduling_form.pools.choices = Pool.choices()
    labels = {'device': 'name', 'link': 'name'}
    if 'view_options' in request.form:
        labels = {
            'device': request.form['device_label'],
            'link': request.form['link_label']
        }
    if len(Device.query.all()) < 50:
        view = 'glearth'
    elif len(Device.query.all()) < 2000:
        view = 'leaflet'
    else:
        view = 'markercluster'
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
        view_options_form=ViewOptionsForm(request.form),
        google_earth_form=GoogleEarthForm(request.form),
        add_device_form=AddDevice(request.form),
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


@blueprint.route('/export_to_google_earth', methods=['POST'])
@login_required
@permission_required('Views section', redirect=False)
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


@blueprint.route('/get_logs/<device_id>', methods=['POST'])
@login_required
def get_logs(device_id):
    device = retrieve(Device, id=device_id)
    device_logs = [
        log.content for log in Log.query.all()
        if log.source == device.ip_address
    ]
    return jsonify('\n'.join(device_logs))
