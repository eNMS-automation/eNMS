#!/bin/sh

exec gunicorn --config=gunicorn.py app:app
