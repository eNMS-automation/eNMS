from flask import Flask, render_template, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from werkzeug.utils import secure_filename
from inspect import stack
from os.path import abspath, dirname, join
from datetime import datetime
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

# start the database
db = SQLAlchemy(app)

# start the scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = join(APP_ROOT, 'uploads')
GETTERS_FOLDER = join(APP_ROOT, 'getters')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
                host = device,
                device_type = netmiko_form.data['driver'],
                username = netmiko_form.data['username'],
                password = netmiko_form.data['password'],
                secret = netmiko_form.data['secret'],
                global_delay_factor = netmiko_form.data['global_delay_factor'],
                port = netmiko_form.data['port'],
                )
            netmiko_handler.send_config_set(script.splitlines())
    return render_template(
                           'netmiko/netmiko.html',
                           form = netmiko_form
                           )

@app.route('/about')
def about():
    return render_template('other/about.html')
    
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
        if scheduler_interval:
            scheduler.add_job(
                            id = ''.join(selected_devices) + scheduler_interval,
                            func = retrieve_and_store_napalm_getters,
                            args = [                            
                                    getters,
                                    selected_devices,
                                    form.data['username'],
                                    form.data['password'],
                                    form.data['secret'],
                                    form.data['port'],
                                    form.data['protocol'].lower()
                                    ],
                            trigger = 'interval',
                            seconds = scheduler_choices[scheduler_interval],
                            replace_existing = True
                            )
        else:
            napalm_output = retrieve_napalm_getters(
                                    getters,
                                    selected_devices,
                                    form.data['username'],
                                    form.data['password'],
                                    form.data['secret'],
                                    form.data['port'],
                                    form.data['protocol'].lower()
                                    )
            form.output.data = '\n\n'.join(napalm_output)
    return render_template(
                           'napalm/napalm_getters.html',
                           form = form
                           )
                           
def send_napalm_script(script, action, devices, *credentials):
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
        if scheduler_date:
            scheduler.add_job(
                            id = script + scheduler_date,
                            func = send_napalm_script,
                            args = [                            
                                    script,
                                    action,
                                    selected_devices,
                                    form.data['username'],
                                    form.data['password'],
                                    form.data['secret'],
                                    form.data['port'],
                                    form.data['protocol'].lower()
                                    ],
                            trigger = 'date',
                            run_date = scheduler_date
                            )
        else:
            send_napalm_script(
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
    import logging
    logging.basicConfig(filename='error.log',level=logging.DEBUG)

if __name__ == '__main__':
    init_db()
    # clear_db()
    # run flask on port 5100
    port = int(os.environ.get('PORT', 5100))
    
    app.run(host='0.0.0.0', port=port, use_reloader=False)
