#!/bin/bash

# Wait for database to be available
if [ "$DATABASE" = "postgres" ]; then
    echo "Waiting for PostgreSQL..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL available"
fi

# Apply migrations
python manage.py migrate

# Start Gunicorn
exec gunicorn task_tracker.wsgi:application --bind 0.0.0.0:8000