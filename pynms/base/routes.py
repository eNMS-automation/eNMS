from collections import Counter
from flask import Blueprint, redirect, render_template, request, url_for
from main import db, login_manager
from objects.models import Node, Link
import flask_login

blueprint = Blueprint(
    'base_blueprint', 
    __name__, 
    url_prefix = '', 
    template_folder = 'templates'
    )

## Custom template rendering

# modified template rendering that includes the username as an argument
# it is used by the sidebar as well as the top navigation 
def _render_template(*args, **kwargs):
    try: 
        kwargs['user'] = flask_login.current_user.username
    except AttributeError:
        # 'AnonymousUserMixin' object has no attribute 'username'
        pass
    return render_template(*args, **kwargs)

## Tear down SQLAlchemy 

@blueprint.teardown_request
def shutdown_session(exception=None):
    db.session.remove()
    
## Login / registration

@blueprint.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'GET':
        form = CreateAccountForm(request.form)
        return _render_template('login/create_account.html', form=form)
    else:
        login_form = LoginForm(request.form)
        user = User(**request.form)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

@blueprint.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = db.session.query(User).filter_by(username=username).first()
        if user and request.form['password'] == user.password:
            flask_login.login_user(user)
            return redirect(url_for('dashboard'))
        return render_template('errors/page_403.html')
    if not flask_login.current_user.is_authenticated:
        login_form = LoginForm(request.form)
        return _render_template('login/login.html', login_form=login_form)
    return redirect(url_for('base_blueprint.dashboard'))
        
@blueprint.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'
    
@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('errors/page_403.html')

@blueprint.route('/dashboard')
@flask_login.login_required
def dashboard():
    # nodes properties
    node_counters = {
        property: 
            Counter(
                map(
                    lambda o: str(getattr(o, property)), 
                    Node.query.all()
                    )
                )
        for property in ('vendor', 'operating_system', 'os_version')
        }
    # link properties
    link_counters = {
        property: 
            Counter(
                map(
                    lambda o: str(getattr(o, property)), 
                    Link.query.all()
                    )
                )
        for property in ('type',)
        }
    return _render_template(
        'home/index.html', 
        node_counters = node_counters,
        link_counters = link_counters
        )
