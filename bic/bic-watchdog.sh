#!/bin/bash

# Configuration
# The 'bic-web' service name assumes you are running the webapp as a systemd service.
SERVICES=("bird" "wg-quick@wg0" "bic-web") 
LOG_FILE="/var/log/bic-watchdog.log" # Changed to a more standard log location

# Ensure log file exists and has correct permissions
touch $LOG_FILE
chmod 644 $LOG_FILE

echo "[$(date)] Running BIC Infrastructure Watchdog..." >> $LOG_FILE

for SVC in "${SERVICES[@]}"; do
    if ! systemctl is-active --quiet "$SVC"; then
        echo "[$(date)] ⚠ $SVC is DOWN. Attempting restart..." >> $LOG_FILE
        systemctl restart "$SVC"
        
        # Verify if restart worked
        sleep 2
        if systemctl is-active --quiet "$SVC"; then
            echo "[$(date)] ✔ $SVC successfully restarted." >> $LOG_FILE
        else
            echo "[$(date)] ✘ $SVC FAILED to restart. Manual intervention required." >> $LOG_FILE
        fi
    fi
done
