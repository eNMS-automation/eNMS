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

 # go to the source directory
 cd source

 # start the server:
 python flask_app.py


Start eNMS with gunicorn (better)
---------------------------------

::

 # start gunicorn
 gunicorn --chdir app --config ./gunicorn_config.py flask_app:app


Start eNMS as a docker container (even better)
----------------------------------------------

::

 # download & run the container
 docker run -d -p 5100:5100 --name enms --restart always afourmy/enms

Once eNMS is running, go to http://127.0.0.1:5100
-------------------------------------------------
