#!/bin/bash
cd /opt/ACT

source /opt/venv/bin/activate

exec gunicorn --bind 127.0.0.1:8000 --workers 4 --timeout 120 atc_monitor.wsgi:application