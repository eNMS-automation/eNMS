from flask import current_app, jsonify, request
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
from eNMS.base.properties import device_subtypes, link_subtype_to_color
from eNMS.objects.forms import AddDevice, AddLink
from eNMS.views import bp, styles
from eNMS.views.forms import GoogleEarthForm


@get(bp, '/<view_type>_view', 'View', ['GET', 'POST'])
def view(view_type):
    devices = fetch_all('Device')
    return dict(
        template=f'{view_type}_view.html',
        pools=fetch_all('Pool'),
        parameters=get_one('Parameters').serialized,
        view=request.form.get(
            'view',
            ('3D', ('2D', '2DC')[len(devices) > 2000])[len(devices) > 50]
        ),
        google_earth_form=GoogleEarthForm(request.form),
        add_device_form=AddDevice(request.form),
        add_link_form=AddLink(request.form, 'Link'),
        device_subtypes=device_subtypes,
        link_colors=link_subtype_to_color,
        name_to_id={d.name: id for id, d in enumerate(devices)},
        devices=serialize('Device'),
        links=serialize('Link')
    )


@get(bp, '/export_to_google_earth', 'View')
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


@post(bp, '/get_logs/<device_id>', 'View')
def get_logs(device_id):
    device_logs = [
        log.content for log in fetch_all('Log')
        if log.source == fetch('Device', id=device_id).ip_address
    ]
    return jsonify('\n'.join(device_logs) or True)
