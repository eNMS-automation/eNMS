from pathlib import Path
from pytest import fixture
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread
from time import sleep

from config import config_dict
from eNMS import create_app, db


@fixture
def base_client():
    app = create_app(Path.cwd(), config_dict['Debug'])
    app_context = app.app_context()
    app_context.push()
    db.session.close()
    db.drop_all()
    yield app.test_client()


@fixture
def user_client():
    app = create_app(Path.cwd(), config_dict['Debug'])
    app_context = app.app_context()
    app_context.push()
    db.session.close()
    db.drop_all()
    client = app.test_client()
    login = {'name': 'admin', 'password': 'admin'}
    with app.app_context():
        client.post('/admin/login', data=login)
        yield client


@fixture
def selenium_client():
    app = create_app(Path.cwd(), config_dict['Debug'])
    app_context = app.app_context()
    app_context.push()
    db.session.close()
    db.drop_all()
    options = Options()
    options.add_argument('--headless')
    client = None
    try:
        client = webdriver.Chrome(
            './tests/chromedriver',
            chrome_options=options
        )
    except Exception:
        pass
    if client:
        t = Thread(
            target=app.run,
            kwargs={
                'host': '0.0.0.0',
                'port': 5000,
                'use_reloader': False
            }
        )
        t.daemon = True
        t.start()
        sleep(1)
        yield client
        client.get('http://0.0.0.0:5000/shutdown')
        client.quit()
    app_context.pop()
