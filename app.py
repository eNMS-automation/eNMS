from __future__ import print_function
from flask import Flask, render_template, request, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from inspect import stack
from os.path import abspath, dirname, join
from datetime import datetime
from subprocess import Popen
import json
import logging
import os
import sys
import xlrd

# prevent python from writing *.pyc files / __pycache__ folders
sys.dont_write_bytecode = True

path_app = dirname(abspath(stack()[0][1]))
if path_app not in sys.path:
    sys.path.append(path_app)

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = join(APP_ROOT, 'uploads')
GETTERS_FOLDER = join(APP_ROOT, 'getters')
APPS_FOLDER = join(APP_ROOT, 'applications')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from forms import *
from models import *
from helpers import *
from database import init_db, clear_db
from jinja2 import Template
from yaml import load

## Tear down SQLAlchemy 

@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()

## Route to any template

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/ajax_connection_to_device', methods = ['POST'])
def ajax_request():
    ip_address = request.form['ip_address']
    path_putty = join(APPS_FOLDER, 'putty.exe')
    ssh_connection = '{} -ssh {}'.format(path_putty, ip_address)
    connect = Popen(ssh_connection.split())
    return jsonify(ip_address=ip_address)
    
## Users

@app.route('/users')
def users():
    return render_template(
                           'users/overview.html', 
                           fields = User.__table__.columns._data, 
                           users = User.query.all()
                           )
                           
@app.route('/manage_users', methods=['GET', 'POST'])
def create_users():
    add_user_form = AddUser()
    if 'add_user' in request.form:
        user = User(**request.form)
        db.session.add(user)
    if request.method == 'POST':
        db.session.commit()
    return render_template(
                           'users/create_user.html',
                           add_user_form = add_user_form,
                           )
                           
## Devices
    
@app.route('/devices')
def devices():
    links = Link.query.all()
    print(links)
    return render_template(
                           'devices/overview.html', 
                           device_fields = Device.__table__.columns._data, 
                           devices = Device.query.all(),
                           link_fields = Link.__table__.columns._data, 
                           links = Link.query.all()
                           )
                           
@app.route('/device_creation', methods=['GET', 'POST'])
def create_devices():
    add_device_form = AddDevice(request.form)
    add_devices_form = AddDevices(request.form)
    add_link_form = AddLink(request.form)
    if 'add_device' in request.form:
        device = Device(**request.form)
        db.session.add(device)
    elif 'add_devices' in request.form:
        filename = request.files['file'].filename
        if 'file' in request.files and allowed_file(filename, 'devices'):  
            filename = secure_filename(filename)
            filepath = join(app.config['UPLOAD_FOLDER'], filename)
            request.files['file'].save(filepath)
            book = xlrd.open_workbook(filepath)
            sheet = book.sheet_by_index(0)
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                kwargs = dict(zip(properties, sheet.row_values(row_index)))
                db.session.add(Device(**kwargs))
        else:
            flash('no file submitted')
    elif 'add_link' in request.form:
        source = db.session.query(Device)\
                 .filter_by(hostname=request.form['source'])\
                 .first()
        destination = db.session.query(Device)\
                      .filter_by(hostname=request.form['destination'])\
                      .first()
        new_link = Link(source_id=source.id, destination_id=destination.id, source=source, destination=destination)
        db.session.add(new_link)
    if request.method == 'POST':
        db.session.commit()
    all_devices = [(d, d) for d in Device.query.all()]
    add_link_form.source.choices = add_link_form.destination.choices = all_devices
    return render_template(
                           'devices/create_device.html',
                           add_device_form = add_device_form,
                           add_devices_form = add_devices_form,
                           add_link_form = add_link_form
                           )
                           
@app.route('/geographical_view')
def geographical_view():
    fields = tuple(Device.__table__.columns._data)
    devices = Device.query.all()
    table = {}
    for device in devices:
        lines = {field: getattr(device, field) for field in fields}
        table[device] = lines
    links = Link.query.all()
    for link in links:
        print(link.source.longitude, link.source.latitude, link.destination.latitude, link.destination.longitude)
    return render_template(
                           'views/geographical_view.html', 
                           table = table,
                           links = Link.query.all()
                           )
    
# @app.route('/manage_devices', methods=['GET', 'POST'])
# def manage_devices():
#     add_device_form = AddDevice(request.form)
#     add_devices_form = AddDevices(request.form)
#     add_link_form = AddLink(request.form)
#     delete_device_form = DeleteDevice(request.form)
#     if add_device_form.validate_on_submit() and 'add_device' in request.form:
#         device = Device(
#                         hostname = request.form['hostname'], 
#                         IP = request.form['ip_address'], 
#                         OS = request.form['os']
#                         )
#         db.session.add(device)
#     elif 'add_devices' in request.form:
#         filename = request.files['file'].filename
#         if 'file' in request.files and allowed_file(filename, 'devices'):  
#             filename = secure_filename(filename)
#             filepath = join(app.config['UPLOAD_FOLDER'], filename)
#             request.files['file'].save(filepath)
#             book = xlrd.open_workbook(filepath)
#             sheet = book.sheet_by_index(0)
#             for row_index in range(1, sheet.nrows):
#                 db.session.add(Device(*sheet.row_values(row_index)))
#         else:
#             flash('no file submitted')
#     elif 'delete' in request.form:
#         selection = delete_device_form.data['devices']
#         db.session.query(Device).filter(Device.IP.in_(selection))\
#         .delete(synchronize_session='fetch')
#     if request.method == 'POST':
#         db.session.commit()
#     # before rendering the page, we update the list of all devices 
#     all_devices = [(d, d) for d in Device.query.all()]
#     delete_device_form.devices.choices = all_devices
#     add_link_form.source.choices = add_link_form.destination.choices = all_devices
#     return render_template(
#                            'devices/manage_devices.html',
#                            add_device_form = add_device_form,
#                            add_devices_form = add_devices_form,
#                            add_link_form = add_link_form,
#                            delete_device_form = delete_device_form
#                            )
                           
@app.route('/netmiko', methods=['GET', 'POST'])
def netmiko():
    netmiko_form = NetmikoForm(request.form)
    # update the list of available devices by querying the database
    netmiko_form.devices.choices = [(d, d) for d in Device.query.all()]
    if 'send' in request.form:
        # if user does not select file, browser also
        # submit a empty part without filename
        filename = request.files['file'].filename
        # retrieve the raw script: we will use it as-is or update it depending
        # on whether a Jinja2 template was uploaded by the user or not
        raw_script = request.form['raw_script']
        if 'file' in request.files and filename:
            if allowed_file(filename, 'netmiko'):
                filename = secure_filename(filename)
                filepath = join(app.config['UPLOAD_FOLDER'], filename)
                with open(filepath, 'r') as f:
                    parameters = load(f)
                template = Template(raw_script)
                script = template.render(**parameters)
            else:
                flash('file {}: format not allowed'.format(filename))
        else:
            script = raw_script
        selected_devices = netmiko_form.data['devices']
        for device in selected_devices:
            device_object = db.session.query(Device)\
                            .filter_by(hostname=device)\
                            .first()
            netmiko_handler = device_object.netmiko_connection(
                host = device,
                device_type = netmiko_form.data['driver'],
                username = netmiko_form.data['username'],
                password = netmiko_form.data['password'],
                secret = netmiko_form.data['secret'],
                global_delay_factor = netmiko_form.data['global_delay_factor']
                )
            netmiko_handler.send_config_set(script.splitlines())
    return render_template(
                           'netmiko/netmiko.html',
                           form = netmiko_form
                           )
    
def retrieve_napalm_getters(getters, devices, *credentials):
    napalm_output = []
    for device in devices:
        napalm_output.append('\n{}\n'.format(device))
        device_object = db.session.query(Device)\
                        .filter_by(hostname=device)\
                        .first()
        try:
            napalm_device = device_object.napalm_connection(*credentials)
            for getter in getters:
                try:
                    output = str_dict(getattr(napalm_device, getters_mapping[getter])())
                except Exception as e:
                    output = '{} could not be retrieve because of {}'.format(getter, e)
                napalm_output.append(output)
        except Exception as e:
            output = 'could not be retrieve because of {}'.format(e)
            napalm_output.append(output)
    return napalm_output
    
def retrieve_and_store_napalm_getters(getters, devices, *credentials):
    # create folder with the current timestamp
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    folder = join(GETTERS_FOLDER, current_time)
    os.makedirs(folder)
    output = retrieve_napalm_getters(getters, devices, *credentials)
    with open(join(folder, 'output.txt'), 'w') as f:
        print('\n\n'.join(output), file=f)

@app.route('/napalm_getters', methods=['GET', 'POST'])
def napalm_getters():
    form = NapalmGettersForm(request.form)
    form.devices.choices = [(d, d) for d in Device.query.all()]
    if 'napalm_query' in request.form:
        selected_devices = form.data['devices']
        getters = form.data['functions']
        scheduler_interval = form.data['scheduler']
        napalm_output = retrieve_napalm_getters(
                                getters,
                                selected_devices,
                                form.data['username'],
                                form.data['password'],
                                form.data['secret'],
                                form.data['protocol'].lower()
                                )
        form.output.data = '\n\n'.join(napalm_output)
    return render_template(
                           'napalm/napalm_getters.html',
                           form = form
                           )
                           
def send_napalm_script(script, action, devices, *credentials):
    napalm_output = []
    for device in devices:
        device_object = db.session.query(Device)\
                        .filter_by(hostname=device)\
                        .first()
        try:
            napalm_device = device_object.napalm_connection(*credentials)
            if action in ('load_merge_candidate', 'load_replace_candidate'):
                getattr(napalm_device, action)(config=script)
            else:
                getattr(napalm_device, action)()
        except Exception as e:
            output = 'exception {}'.format(e)
            napalm_output.append(output)
    return '\n\n'.join(napalm_output)
                           
@app.route('/napalm_configuration', methods=['GET', 'POST'])
def napalm_configuration():
    form = NapalmParametersForm(request.form)
    # update the list of available devices by querying the database
    form.devices.choices = [(d, d) for d in Device.query.all()]
    if 'send' in request.form:
        # if user does not select file, browser also
        # submit a empty part without filename
        filename = request.files['file'].filename
        # retrieve the raw script: we will use it as-is or update it depending
        # on whether a Jinja2 template was uploaded by the user or not
        raw_script = request.form['raw_script']
        if 'file' in request.files and filename:
            if allowed_file(filename, 'netmiko'):
                filename = secure_filename(filename)
                filepath = join(app.config['UPLOAD_FOLDER'], filename)
                with open(filepath, 'r') as f:
                    parameters = load(f)
                template = Template(raw_script)
                script = template.render(**parameters)
            else:
                flash('file {}: format not allowed'.format(filename))
        else:
            script = raw_script
        selected_devices = form.data['devices']
        action = napalm_actions[form.data['actions']]
        scheduler_date = form.data['scheduler']
        form.raw_script.data = send_napalm_script(
                                    script,
                                    action,
                                    selected_devices,
                                    form.data['username'],
                                    form.data['password'],
                                    form.data['secret'],
                                    form.data['port'],
                                    form.data['protocol'].lower()
                                    )
    return render_template(
                           'napalm/napalm_configuration.html',
                           form = form
                           )

@app.route('/<template>')
def route_template(template):
    return render_template(template)
    
## 

## Errors

@app.errorhandler(403)
def not_found_error(error):
    return render_template('page_403.html'), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('page_404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('page_500.html'), 500

## Logs

if not app.debug:
    logging.basicConfig(filename='error.log',level=logging.DEBUG)

if __name__ == '__main__':
    init_db()

    # run flask on port 5100
    port = int(os.environ.get('PORT', 5100))
    
    app.run(host='0.0.0.0', port=port)
