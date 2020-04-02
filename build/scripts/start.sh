FLASK_APP="app.py"
FLASK_DEBUG=1
cd /media/sf_shared/eNMS/
gunicorn --config gunicorn.py app:app