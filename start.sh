#!/bin/sh
cd /data/semantic-lsicluster-service

LOGS_DIR=logs
if [ ! -d "${LOGS_DIR}" ]
then
  mkdir "${LOGS_DIR}"
fi

python3 semantic-lsicluster-service.py

echo "semantic-lsicluster-service starting..."
