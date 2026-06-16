#!/bin/bash
set -e
echo "Starting Celery worker..."
exec celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
