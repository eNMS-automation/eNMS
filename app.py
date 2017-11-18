from flask import Flask, render_template, request, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from inspect import stack
from os.path import abspath, dirname, join
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
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# dict that maps an IP address to a Device object
devices = {}
# all variables used for sending script with netmiko
variables = {}

from forms import *
from models import *
from helpers import *
from database import init_db, clear_db
from jinja2 import Template
from yaml import load

# automatically tear down SQLAlchemy.
@app.teardown_request
def shutdown_session(exception=None):
    db.session.commit()
    db.session.remove()

# login required decorator.
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap

@app.route('/')
def home():
    return render_template('other/home.html')
    
@app.route('/devices')
def devices():
    return render_template('devices/devices.html', devices=Device.query.all())
    
@app.route('/manage_devices', methods=['GET', 'POST'])
def manage_devices():
    add_device_form = AddDevice(request.form)
    add_devices_form = AddDevices(request.form)
    delete_device_form = DeleteDevice(request.form)
    if add_device_form.validate_on_submit() and 'add_device' in request.form:
        device = Device(
                        hostname = request.form['hostname'], 
                        IP = request.form['ip_address'], 
                        OS = request.form['os']
                        )
        db.session.add(device)
    elif 'add_devices' in request.form:
        print(request.files, file=sys.stderr)
        filename = request.files['file'].filename
        if 'file' in request.files and allowed_file(filename, 'devices'):  
            filename = secure_filename(filename)
            filepath = join(app.config['UPLOAD_FOLDER'], filename)
            request.files['file'].save(filepath)
            book = xlrd.open_workbook(filepath)
            sheet = book.sheet_by_index(0)
            for row_index in range(1, sheet.nrows):
                db.session.add(Device(*sheet.row_values(row_index)))
        else:
            flash('no file submitted')
    elif 'delete' in request.form:
        selection = delete_device_form.data['devices']
        db.session.query(Device).filter(Device.IP.in_(selection))\
        .delete(synchronize_session='fetch')
    if request.method == 'POST':
        db.session.commit()
    # before rendering the page, we update the list of all devices 
    delete_device_form.devices.choices = [(d, d) for d in Device.query.all()]
    return render_template(
                           'devices/manage_devices.html',
                           add_device_form = add_device_form,
                           add_devices_form = add_devices_form,
                           delete_device_form = delete_device_form
                           )
                           
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
                                netmiko_form.data['driver'],
                                netmiko_form.data['username'],
                                netmiko_form.data['password'],
                                netmiko_form.data['secret'],
                                netmiko_form.data['global_delay_factor'],
                                )
            netmiko_handler.send_config_set(script.splitlines())
    return render_template(
                           'netmiko/netmiko.html',
                           variables=variables, 
                           devices={},
                           form=netmiko_form
                           )

@app.route('/about')
def about():
    return render_template('other/about.html')
    
@app.route('/napalm_getters', methods=['GET', 'POST'])
def napalm_getters():
    napalm_getters_form = NapalmGettersForm(request.form)
    napalm_getters_form.devices.choices = [(d, d) for d in Device.query.all()]
    if 'napalm_query' in request.form:
        napalm_output = []
        device_hostname = napalm_getters_form.data['devices']
        device_object = db.session.query(Device).filter_by(hostname=device_hostname).first()
        napalm_device = device_object.napalm_connection() 
        for getter in napalm_getters_form.data['functions']:
            try:
                output = str_dict(getattr(napalm_device, getters_mapping[getter])())
            except Exception as e:
                flash('{} could not be retrieve because of {}'.format(getter, e))
            napalm_output.append(output)
        napalm_getters_form.output.data = '\n\n'.join(napalm_output)
    return render_template(
                           'napalm/napalm_getters.html',
                           form = napalm_getters_form
                           )
                           
@app.route('/napalm_configuration', methods=['GET', 'POST'])
def napalm_configuration():
    parameters_form = NapalmParametersForm(request.form)
    # update the list of available devices by querying the database
    parameters_form.devices.choices = [(d, d) for d in Device.query.all()]
    if parameters_form.validate_on_submit():
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
                variable['script'] = template.render(**parameters)
            else:
                flash('file {}: format not allowed'.format(filename))
        else:
            variables['script'] = raw_script
    return render_template(
                           'napalm/napalm_configuration.html',
                           variables=variables, 
                           devices={},
                           form=parameters_form
                           )
                           
@app.route('/napalm_daemon')
def napalm_daemon():
    return render_template('napalm/napalm_daemon.html')
                           
@app.route('/login')
def login():
    form = LoginForm(request.form)
    return render_template('forms/login.html', form=form)

@app.route('/register')
def register():
    form = RegisterForm(request.form)
    return render_template('forms/register.html', form=form)

@app.route('/forgot')
def forgot():
    form = ForgotForm(request.form)
    return render_template('forms/forgot.html', form=form)
    
@app.route("/department", methods=["GET", "POST"])
def department():
    form = TestForm(request.form)
    departments = Department.query.all()
    form.department.choices = [('', 'Select a department')] + [
        (department.id, department.name) for department in departments]
    chosen_department = None
    chosen_employee = None
    
    return render_template('forms/department.html', form=form)

@app.route("/department/<int:department_id>/", methods=["GET"])
def get_request(department_id):
    """
    Handle GET request to - /<department_id>/
    Return a list of tuples - (<employee id>, <employee name>)
    """
    employees = Employee.query.all()

    department_employees = [
                            (employee.id, employee.name) for employee in employees
                            if employee.department_id == department_id
                            ]
    response = make_response(json.dumps(department_employees))
    response.content_type = 'application/json'
    return response

## Error handlers.

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

if not app.debug:
    file_handler = logging.FileHandler('error.log')
    file_handler.setlogging.Formatter(
        logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

if __name__ == '__main__':
    init_db()
    # clear_db()
    # run flask on port 5100
    port = int(os.environ.get('PORT', 5100))
    app.run(host='0.0.0.0', port=port, use_reloader=False)
