#!/bin/bash

set -e

read -p "Migration message: " migration_message

DJANGO_SETTINGS_MODULE=app.settings.development python manage.py makemigrations app -m "$migration_message"

read -p "Migration created. Apply now? [y/N] " confirm
[[ "$confirm" == [yY] ]] && DJANGO_SETTINGS_MODULE=app.settings.development python manage.py migrate
