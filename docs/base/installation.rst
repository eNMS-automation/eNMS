============
Installation
============

First steps
-----------

::

 # download the code from github:
 git clone https://github.com/afourmy/eNMS.git
 cd eNMS

 # install the requirements:
 pip install -r requirements.txt

Start eNMS in debugging mode
----------------------------

::

 # set the FLASK_APP environment variable
 (Windows) set FLASK_APP=app.py
 (Unix) export FLASK_APP=app.py

 # set the FLASK_DEBUG environment variable
 (Windows) set FLASK_DEBUG=1
 (Unix) export FLASK_DEBUG=1

 # run the application
 flask run --host=0.0.0.0


Start eNMS with gunicorn (better)
---------------------------------

::

 # start gunicorn
 gunicorn --config gunicorn.py app:app


Start eNMS as a docker container (even better)
----------------------------------------------

::

 # download & run the container
 docker run -d -p 5000:5000 --name enms --restart always afourmy/enms

Once eNMS is running, go to http://127.0.0.1:5000
-------------------------------------------------
