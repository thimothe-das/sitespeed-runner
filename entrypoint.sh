#!/bin/bash
# Copy bundled scripts to the host-mounted scripts directory
# so the sitespeed.io container (running on the host) can access them
if [ -d /app/scripts-bundled ] && [ -d /app/scripts ]; then
  cp -r /app/scripts-bundled/* /app/scripts/
  echo "Scripts synced to host volume"
fi

exec gunicorn --bind 0.0.0.0:5679 --workers 1 --threads 4 --timeout 600 app:app
