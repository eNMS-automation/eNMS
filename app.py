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
from database import init_db
from helpers import napalm_dispatcher
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
    return render_template('pages/home.html')
    
@app.route('/devices')
def devices():
    devices = Device.query.all()
    return render_template('pages/devices.html', devices=devices)
    
@app.route('/add_devices')
def add_devices():
    return render_template('pages/add_devices.html')

@app.route('/about')
def about():
    return render_template('pages/about.html')
    
@app.route('/napalm')
def napalm():
    return render_template('pages/napalm.html')

@app.route('/netmiko', methods=['GET', 'POST'])
def netmiko():
    form = NetmikoParametersForm(request.form)
    print(form.errors, form.validate_on_submit(), file=sys.stderr)
    if form.validate_on_submit() and 'test' in request.form:
        print(request.files, file=sys.stderr)
        # if user does not select file, browser also
        # submit a empty part without filename
        filename = request.files['file'].filename
        if 'file' in request.files and filename:
            if allowed_file(filename, 'netmiko'):
                filename = secure_filename(filename)
                filepath = join(app.config['UPLOAD_FOLDER'], filename)
                with open(filepath, 'r') as f:
                    test = load(f)
                    print(test, file=sys.stderr)
    return render_template(
                           'pages/netmiko.html', 
                           variables={'script': 'aa'}, 
                           devices={},
                           form=form
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
    
def populate_db():
    db.session.query(Device).delete()
    db.session.query(Department).delete()
    db.session.query(Employee).delete()
    db.session.commit()
    for hostname, (IP, OS) in napalm_dispatcher.items():
        device = Device(hostname, IP, OS)
        db.session.add(device)
    db.session.commit()
    for dep, employees in {'a': ('1', '2'), 'b': ('3', '4'), 'c': ('i',)}.items():
        department = Department(dep)
        db.session.add(department)
        db.session.flush()
        for employee in employees:
            e = Employee(employee, department.id)
            db.session.add(e)
    db.session.commit()

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
    populate_db()
    # run flask on port 5100
    port = int(os.environ.get('PORT', 5100))
    app.run(host='0.0.0.0', port=port)
