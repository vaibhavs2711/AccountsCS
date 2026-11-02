#!/bin/bash
# Backup script for Cityscope Accounts database
# To be run on the Zima server via cron

# Get the absolute path to the directory where this script is located
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKUP_DIR="$PROJECT_DIR/backups"

# Create the backups directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate a timestamp for the backup filename
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Execute mysqldump inside the docker container and save it to the backups folder
docker exec cityscope-db mysqldump -u root -pcityscope-secure-db-pass cityscope_accounts > "$BACKUP_FILE"

# Clean up old backups: Keep backups from the last 30 days, delete older ones
find "$BACKUP_DIR" -name "db_backup_*.sql" -type f -mtime +30 -exec rm {} \;
