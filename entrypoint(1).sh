#!/bin/sh

echo "Waiting for MySQL database..."
# Python database connectivity checker
python -c "
import time, pymysql, os, sys
host = os.environ.get('MYSQL_HOST', 'localhost')
port = int(os.environ.get('MYSQL_PORT', 3306))
user = os.environ.get('MYSQL_USER', 'root')
pwd = os.environ.get('MYSQL_PASSWORD', 'root')
for i in range(30):
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=pwd)
        conn.close()
        print('MySQL connection established!')
        sys.exit(0)
    except Exception as e:
        print(f'Waiting for MySQL... attempt {i+1}/30 ({e})')
        time.sleep(2)
sys.exit(1)
"

if [ $? -eq 0 ]; then
  echo "Database is ready. Running seed script..."
  python seed.py
  echo "Starting application with Gunicorn (2 workers)..."
  exec gunicorn -w 2 -b 0.0.0.0:5000 app:app
else
  echo "Error: MySQL did not respond in time. Exiting."
  exit 1
fi
