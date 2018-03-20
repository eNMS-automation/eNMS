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

 # download the docker image
 docker pull afourmy/enms

 # find the name of the docker image
 docker images

 # run the image on port 5100
 docker run -p 5100:5100 image_name