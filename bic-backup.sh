#!/bin/bash

# --- CONFIGURATION ---
# The root of the project, assuming this script is in the project root.
BIC_DIR=$(pwd)
BACKUP_DIR="$HOME/bic-backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_NAME="bic_backup_$TIMESTAMP.tar.gz"
RETENTION_DAYS=30

# --- PREPARATION ---
mkdir -p "$BACKUP_DIR"

echo "----------------------------------------------------"
echo " BIC IPAM: Automated Backup System"
echo " Started: $(date)"
echo "----------------------------------------------------"

# --- EXECUTION ---
echo "Creating archive: $BACKUP_NAME..."

# Archive the SQLite database and any other critical configs.
# We will archive the main ipam.db and the entire bic directory for simplicity.
tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    -C "$BIC_DIR" ipam.db \
    -C "$BIC_DIR" bic

if [ $? -eq 0 ]; then
    echo "✔ Backup successful: $BACKUP_DIR/$BACKUP_NAME"
else
    echo "✘ Backup FAILED!"
    exit 1
fi

# --- CLEANUP (Retention) ---
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "bic_backup_*.tar.gz" -mtime +$RETENTION_DAYS -exec rm {} \;

echo "----------------------------------------------------"
echo " Backup Operation Complete."
echo "----------------------------------------------------"
