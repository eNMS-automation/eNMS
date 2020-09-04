#!/bin/bash
exec gunicorn -c gunicorn.py app:app