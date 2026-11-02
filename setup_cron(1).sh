#!/bin/bash
# Run this script on your Zima server to automatically configure the weekly backup schedule.

# Make sure the backup script is executable
chmod +x /DATA/apps/AccountsCS/backup.sh

CRON_JOB="0 0 * * 0 /DATA/apps/AccountsCS/backup.sh"

# Check if the cron job already exists to prevent duplicates
if crontab -l 2>/dev/null | grep -F "$CRON_JOB" > /dev/null; then
    echo "✅ Cron job already exists!"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Backup scheduled successfully! It will run every Sunday at midnight."
fi
