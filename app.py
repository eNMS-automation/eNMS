from flask import Flask, render_template, request, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from inspect import stack
from os.path import abspath, dirname, join
import json
import logging
import os
import sys

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

# allowed extensions depending on the webpage
allowed_extensions = {'devices': {'xls'}, 'netmiko': {'yaml'}}

# dict that maps an IP address to a Device object
devices = {}
# all variables used for sending script with netmiko
variables = {}

def allowed_file(name, webpage):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions[webpage]
    return allowed_syntax and allowed_extension

from forms import *
from models import *
from database import init_db, clear_db
from netmiko import ConnectHandler
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
    elif 'delete' in request.form:
        selection = delete_device_form.data['devices']
        db.session.query(Device).filter(Device.IP.in_(selection))\
        .delete(synchronize_session='fetch')
    if request.method == 'POST':
        db.session.commit()
        delete_device_form.devices.choices = [(str(d), str(d)) for d in Device.query.all()]
        return render_template(
                                'devices/manage_devices.html',
                                add_device_form = add_device_form,
                                add_devices_form = add_devices_form,
                                delete_device_form = delete_device_form
                                )
    return render_template(
                           'devices/manage_devices.html',
                           add_device_form = add_device_form,
                           add_devices_form = add_devices_form,
                           delete_device_form = delete_device_form
                           )

@app.route('/about')
def about():
    return render_template('other/about.html')
    
@app.route('/napalm_getters')
def napalm_getters():
    napalm_getters_form = NapalmGettersForm(request.form)
    napalm_getters_form.devices.choices = [(d, d) for d in Device.query.all()]
    return render_template(
                           'napalm/napalm_getters.html',
                           form = napalm_getters_form
                           )
                           
@app.route('/napalm_configuration')
def napalm_configuration():
    return render_template('napalm/napalm_configuration.html')
                           
@app.route('/napalm_daemon')
def napalm_daemon():
    return render_template('napalm/napalm_daemon.html')

@app.route('/netmiko', methods=['GET', 'POST'])
def netmiko():
    parameters_form = NetmikoParametersForm(request.form)
    device_selection_form = NetmikoDevicesForm(request.form)
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
                print('file not allowed')
        else:
            variables['script'] = raw_script
        # before rendering the second step, update the list of available
        # devices by querying the database, and the script
        device_selection_form.devices.choices = [(d, d) for d in Device.query.all()]
        device_selection_form.script.data = variables['script']
        return render_template(
                               'netmiko/netmiko_step2.html',
                               variables=variables, 
                               devices={},
                               form=device_selection_form
                               )
    return render_template(
                           'netmiko/netmiko_step1.html',
                           variables=variables, 
                           devices={},
                           form=parameters_form
                           )
                           
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
    print(departments, file=sys.stderr)
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
