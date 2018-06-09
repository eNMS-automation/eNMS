from flask_login import login_required
from passlib.hash import cisco_type7
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from tacacs_plus.client import TACACSClient
from tacacs_plus.flags import TAC_PLUS_AUTHEN_TYPE_ASCII
import flask_login


from eNMS import db
from eNMS.admin import blueprint
from eNMS.admin.forms import (
    AddUser,
    CreateAccountForm,
    LoginForm,
    GeographicalParametersForm,
    SyslogServerForm,
    TacacsServerForm,
)
from eNMS.admin.models import Parameters, SyslogServer, User, user_factory, TacacsServer
from eNMS.admin.properties import user_properties, user_search_properties
from eNMS.base.helpers import get_obj
from eNMS.base.properties import pretty_names
from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    url_for
)


## Template rendering


@blueprint.route('/user_management')
@login_required
def users():
    form = AddUser(request.form)
    return render_template(
        'users_overview.html',
        fields=user_search_properties,
        names=pretty_names,
        users=User.serialize(),
        form=form
    )


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = str(request.form['name'])
        password = str(request.form['password'])
        user = db.session.query(User).filter_by(name=name).first()
        if user and cisco_type7.verify(password, user.password):
            flask_login.login_user(user)
            return redirect(url_for('base_blueprint.dashboard'))
        else:
            try:
                # tacacs_plus does not support py2 unicode, hence the
                # conversion to string.
                # TACACSClient cannot be saved directly to session
                # as it is not serializable: this temporary fixes will create
                # a new instance of TACACSClient at each TACACS connection
                # attemp: clearly suboptimal, to be improved later.
                encrypted_password = cisco_type7.hash(password)
                tacacs_server = db.session.query(TacacsServer).one()
                tacacs_client = TACACSClient(
                    str(tacacs_server.ip_address),
                    int(tacacs_server.port),
                    str(cisco_type7.decode(str(tacacs_server.password)))
                )
                if tacacs_client.authenticate(
                    name,
                    password,
                    TAC_PLUS_AUTHEN_TYPE_ASCII
                ).valid:
                    user = User(name=name, password=encrypted_password)
                    db.session.add(user)
                    db.session.commit()
                    flask_login.login_user(user)
                    return redirect(url_for('base_blueprint.dashboard'))
            except NoResultFound:
                pass
        return render_template('errors/page_403.html')
    if not flask_login.current_user.is_authenticated:
        return render_template(
            'login.html',
            login_form=LoginForm(request.form),
            create_account_form=CreateAccountForm(request.form)
        )
    return redirect(url_for('base_blueprint.dashboard'))


@blueprint.route('/logout')
@login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for('admin_blueprint.login'))


@blueprint.route('/administration')
@login_required
def admninistration():
    try:
        tacacs_server = db.session.query(TacacsServer).one()
    except NoResultFound:
        tacacs_server = None
    try:
        syslog_server = db.session.query(SyslogServer).one()
    except NoResultFound:
        syslog_server = None
    return render_template(
        'administration.html',
        tacacs_form=TacacsServerForm(request.form),
        syslog_form=SyslogServerForm(request.form),
        tacacs_server=tacacs_server,
        syslog_server=syslog_server
    )


@blueprint.route('/parameters')
@login_required
def parameters():
    return render_template(
        'parameters.html',
        geographical_parameters_form=GeographicalParametersForm(request.form),
        parameters=db.session.query(Parameters).one()
    )


## AJAX calls


@blueprint.route('/process_user', methods=['POST'])
def process_user():
    return jsonify(user_factory(**request.form.to_dict()).serialized)


@blueprint.route('/get_<user_id>', methods=['POST'])
@login_required
def get_user(user_id):
    user = get_obj(User, id=user_id)
    return jsonify(user.serialized)


@blueprint.route('/delete_<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = get_obj(User, id=user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(user.name)


@blueprint.route('/save_tacacs_server', methods=['POST'])
@login_required
def save_tacacs_server():
    TacacsServer.query.delete()
    tacacs_server = TacacsServer(**request.form.to_dict())
    db.session.add(tacacs_server)
    db.session.commit()
    return jsonify({})


@blueprint.route('/save_syslog_server', methods=['POST'])
@login_required
def save_syslog_server():
    SyslogServer.query.delete()
    syslog_server = SyslogServer(**request.form.to_dict())
    db.session.add(syslog_server)
    db.session.commit()
    return jsonify({})


@blueprint.route('/save_geographical_parameters', methods=['POST'])
@login_required
def save_parameters():
    parameters = db.session.query(Parameters).one()
    parameters.update(**request.form.to_dict())
    db.session.commit()
    return jsonify({})
