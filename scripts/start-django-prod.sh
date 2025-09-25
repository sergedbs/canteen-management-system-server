#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --chdir=/app
