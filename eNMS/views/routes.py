from flask import current_app, jsonify, render_template, request
from os.path import join
from simplekml import Kml

from eNMS.base.helpers import (
    fetch,
    fetch_all,
    get,
    get_one,
    post,
    serialize
)
from eNMS.base.properties import (
    device_public_properties,
    device_subtypes,
    link_public_properties,
    link_subtype_to_color,
    pretty_names
)
from eNMS.objects.forms import AddDevice, AddLink
from eNMS.views import bp, styles
from eNMS.views.forms import GoogleEarthForm, ViewOptionsForm


@get(bp, '/<view_type>_view', 'Views Section', ['GET', 'POST'])
def view(view_type):
    devices = fetch_all('Device')
    add_link_form = AddLink(request.form)
    form_devices = [(l.name, l.name) for l in fetch_all('Device')]
    add_link_form.source_name.choices = form_devices
    add_link_form.destination_name.choices = form_devices
    labels = {'device': 'name', 'link': 'name'}
    if 'view_options' in request.form:
        labels = {
            'device': request.form['device_label'],
            'link': request.form['link_label']
        }
    if len(devices) < 50:
        view = 'glearth'
    elif len(devices) < 2000:
        view = 'leaflet'
    else:
        view = 'markercluster'
    if 'view' in request.form:
        view = request.form['view']
    name_to_id = {device.name: id for id, device in enumerate(devices)}
    return render_template(
        f'{view_type}_view.html',
        pools=fetch_all('Pool'),
        parameters=get_one('Parameters').serialized,
        view=view,
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
        devices=serialize('Device'),
        links=serialize('Link')
    )


@get(bp, '/export_to_google_earth', 'Views Section')
def export_to_google_earth():
    kml_file = Kml()
    for device in fetch_all('Device'):
        point = kml_file.newpoint(name=device.name)
        point.coords = [(device.longitude, device.latitude)]
        point.style = styles[device.subtype]
        point.style.labelstyle.scale = request.form['label_size']
    for link in fetch_all('Link'):
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
    return jsonify(True)


@post(bp, '/get_logs/<device_id>', 'Logs Section')
def get_logs(device_id):
    device_logs = [
        log.content for log in fetch_all('Log')
        if log.source == fetch('Device', id=device_id).ip_address
    ]
    return jsonify('\n'.join(device_logs) or True)
