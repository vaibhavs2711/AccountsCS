"""
Cityscope Accounts — Production WSGI Server for Windows
Runs the Flask application using Waitress (multi-threaded, production-grade).
"""

import os
from waitress import serve
from app import app

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    threads = int(os.environ.get('THREADS', 6))
    print(f"Starting Cityscope Accounts Production Server on http://{host}:{port} with {threads} worker threads...")
    serve(app, host=host, port=port, threads=threads)
