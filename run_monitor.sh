#!/bin/bash
# Wrapper to run ftp_monitor.py continuously
cd "$(dirname "$0")"
PYTHON=${PYTHON:-python3}
LOG_FILE="ftp_monitor.log"
exec "$PYTHON" ftp_monitor.py --iterations 0 --interval 60 >> "$LOG_FILE" 2>&1
