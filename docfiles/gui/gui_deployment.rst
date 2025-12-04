GUI Deployment Guide
====================

This guide covers deploying the py3plex web interface.

.. danger::

   **Security Warning:** The GUI is in development mode—suitable for local use only. **Do not expose to public internet without proper security hardening.** See `Security Considerations`_ below for required steps before any production deployment.

Overview
--------

The py3plex GUI can be deployed in several ways:

1. **Local Development** - Run directly on your machine
2. **Docker Container** - Isolated, reproducible environment
3. **Production Server** - Behind reverse proxy with TLS
4. **Cloud Deployment** - AWS, Azure, GCP, etc.

See :doc:`gui_user_guide` for basic usage and :doc:`gui_architecture` for technical details.

Local Development Setup
-----------------------

Quick Start
~~~~~~~~~~~

.. code-block:: bash

    # Clone repository
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Install with GUI dependencies
    pip install -e ".[gui]"
    
    # Start development server
    python gui/app.py

The GUI will be available at ``http://localhost:5000``.

Configuration
~~~~~~~~~~~~~

Create a configuration file ``gui/config.py``:

.. code-block:: python

    # Development configuration
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    SECRET_KEY = 'dev-secret-key-change-in-production'
    
    # Upload settings
    UPLOAD_FOLDER = './uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max file size
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'txt', 'edgelist', 'graphml', 'gml', 'json', 'arrow'}

Docker Deployment
-----------------

Basic Docker Setup
~~~~~~~~~~~~~~~~~~

The repository includes a Dockerfile for the GUI:

.. code-block:: bash

    # Build image
    docker build -t py3plex-gui:latest -f gui/Dockerfile .
    
    # Run container
    docker run -d \
      -p 5000:5000 \
      -v $(pwd)/data:/app/data \
      --name py3plex-gui \
      py3plex-gui:latest

The GUI will be available at ``http://localhost:5000``.

Docker Compose
~~~~~~~~~~~~~~

Create ``docker-compose.yml``:

.. code-block:: yaml

    version: '3.8'
    
    services:
      gui:
        build:
          context: .
          dockerfile: gui/Dockerfile
        ports:
          - "5000:5000"
        volumes:
          - ./data:/app/data
          - ./uploads:/app/uploads
        environment:
          - FLASK_ENV=production
          - SECRET_KEY=${SECRET_KEY}
        restart: unless-stopped
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
          interval: 30s
          timeout: 10s
          retries: 3

Start with:

.. code-block:: bash

    # Set secret key
    export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
    
    # Start services
    docker-compose up -d
    
    # Check logs
    docker-compose logs -f gui

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Configure via environment variables:

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Variable
     - Description
     - Default
   * - ``FLASK_ENV``
     - Environment (development/production)
     - development
   * - ``SECRET_KEY``
     - Session secret key (required)
     - None
   * - ``HOST``
     - Bind address
     - 0.0.0.0
   * - ``PORT``
     - Bind port
     - 5000
   * - ``MAX_WORKERS``
     - Worker processes
     - 4
   * - ``UPLOAD_FOLDER``
     - Upload directory
     - ./uploads
   * - ``DATA_FOLDER``
     - Data directory
     - ./data

Production Deployment
---------------------

Using Gunicorn
~~~~~~~~~~~~~~

For production, use a production WSGI server like Gunicorn:

.. code-block:: bash

    # Install Gunicorn
    pip install gunicorn
    
    # Run with Gunicorn
    gunicorn \
      --bind 0.0.0.0:5000 \
      --workers 4 \
      --timeout 120 \
      --access-logfile - \
      --error-logfile - \
      gui.app:app

Supervisor Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

Use Supervisor to manage the GUI process:

Create ``/etc/supervisor/conf.d/py3plex-gui.conf``:

.. code-block:: ini

    [program:py3plex-gui]
    command=/path/to/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 gui.app:app
    directory=/path/to/py3plex
    user=www-data
    autostart=true
    autorestart=true
    redirect_stderr=true
    stdout_logfile=/var/log/py3plex-gui.log
    environment=FLASK_ENV="production",SECRET_KEY="your-secret-key"

Start with:

.. code-block:: bash

    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl start py3plex-gui

Systemd Service
~~~~~~~~~~~~~~~

Alternative: use systemd:

Create ``/etc/systemd/system/py3plex-gui.service``:

.. code-block:: ini

    [Unit]
    Description=Py3plex GUI
    After=network.target
    
    [Service]
    Type=notify
    User=www-data
    WorkingDirectory=/path/to/py3plex
    Environment="FLASK_ENV=production"
    Environment="SECRET_KEY=your-secret-key"
    ExecStart=/path/to/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 gui.app:app
    ExecReload=/bin/kill -s HUP $MAINPID
    KillMode=mixed
    TimeoutStopSec=5
    PrivateTmp=true
    
    [Install]
    WantedBy=multi-user.target

Enable and start:

.. code-block:: bash

    sudo systemctl daemon-reload
    sudo systemctl enable py3plex-gui
    sudo systemctl start py3plex-gui
    sudo systemctl status py3plex-gui

Reverse Proxy Setup
-------------------

Nginx Configuration
~~~~~~~~~~~~~~~~~~~

Configure Nginx as a reverse proxy:

Create ``/etc/nginx/sites-available/py3plex-gui``:

.. code-block:: nginx

    server {
        listen 80;
        server_name py3plex.yourdomain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name py3plex.yourdomain.com;
        
        # SSL certificates (use Let's Encrypt)
        ssl_certificate /etc/letsencrypt/live/py3plex.yourdomain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/py3plex.yourdomain.com/privkey.pem;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        
        # Upload size limit
        client_max_body_size 100M;
        
        location / {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts for long-running operations
            proxy_connect_timeout 300s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }
        
        # Static files (if serving separately)
        location /static {
            alias /path/to/py3plex/gui/static;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

Enable the site:

.. code-block:: bash

    sudo ln -s /etc/nginx/sites-available/py3plex-gui /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx

Apache Configuration
~~~~~~~~~~~~~~~~~~~~

Alternative: use Apache as reverse proxy:

.. code-block:: apache

    <VirtualHost *:80>
        ServerName py3plex.yourdomain.com
        Redirect permanent / https://py3plex.yourdomain.com/
    </VirtualHost>
    
    <VirtualHost *:443>
        ServerName py3plex.yourdomain.com
        
        SSLEngine on
        SSLCertificateFile /etc/letsencrypt/live/py3plex.yourdomain.com/fullchain.pem
        SSLCertificateKeyFile /etc/letsencrypt/live/py3plex.yourdomain.com/privkey.pem
        
        ProxyPreserveHost On
        ProxyPass / http://127.0.0.1:5000/
        ProxyPassReverse / http://127.0.0.1:5000/
        
        # Security headers
        Header always set X-Frame-Options "SAMEORIGIN"
        Header always set X-Content-Type-Options "nosniff"
    </VirtualHost>

SSL/TLS with Let's Encrypt
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Install certbot
    sudo apt-get install certbot python3-certbot-nginx
    
    # Obtain certificate
    sudo certbot --nginx -d py3plex.yourdomain.com
    
    # Auto-renewal (certbot sets this up automatically)
    sudo certbot renew --dry-run

Security Considerations
-----------------------

Secret Key Management
~~~~~~~~~~~~~~~~~~~~~

**Never** hardcode secret keys in code or configuration files:

.. code-block:: bash

    # Generate strong secret key
    python -c 'import secrets; print(secrets.token_hex(32))' > .secret_key
    
    # Set in environment
    export SECRET_KEY=$(cat .secret_key)
    
    # Or use environment file
    echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" > .env

File Upload Security
~~~~~~~~~~~~~~~~~~~~

Configure upload restrictions:

.. code-block:: python

    # In config.py
    ALLOWED_EXTENSIONS = {'txt', 'edgelist', 'graphml', 'gml', 'json', 'arrow'}
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB
    
    # Validate uploads
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

Rate Limiting
~~~~~~~~~~~~~

Implement rate limiting for API endpoints:

.. code-block:: python

    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    @app.route("/api/upload")
    @limiter.limit("10 per hour")
    def upload():
        pass

Authentication
~~~~~~~~~~~~~~

Add user authentication for production:

.. code-block:: python

    from flask_login import LoginManager, login_required
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @app.route("/dashboard")
    @login_required
    def dashboard():
        pass

Monitoring and Logging
----------------------

Application Logging
~~~~~~~~~~~~~~~~~~~

Configure structured logging:

.. code-block:: python

    import logging
    from logging.handlers import RotatingFileHandler
    
    # Configure logging
    handler = RotatingFileHandler(
        'logs/py3plex-gui.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

Prometheus Metrics
~~~~~~~~~~~~~~~~~~

Export metrics for Prometheus:

.. code-block:: python

    from prometheus_flask_exporter import PrometheusMetrics
    
    metrics = PrometheusMetrics(app)
    
    # Custom metrics
    metrics.info('app_info', 'Application info', version='1.0')

Health Checks
~~~~~~~~~~~~~

Implement health check endpoint:

.. code-block:: python

    @app.route('/health')
    def health():
        # Check dependencies
        try:
            # Test database connection, file system, etc.
            return {'status': 'healthy'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 503

Cloud Deployment Examples
--------------------------

AWS EC2
~~~~~~~

1. Launch EC2 instance (Ubuntu 22.04 LTS)
2. Install dependencies
3. Clone repository
4. Follow production deployment steps above
5. Configure security groups (ports 80, 443)

AWS ECS (Docker)
~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "family": "py3plex-gui",
      "containerDefinitions": [{
        "name": "gui",
        "image": "your-registry/py3plex-gui:latest",
        "memory": 2048,
        "cpu": 1024,
        "essential": true,
        "portMappings": [{
          "containerPort": 5000,
          "protocol": "tcp"
        }],
        "environment": [
          {"name": "FLASK_ENV", "value": "production"}
        ],
        "secrets": [
          {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
        ]
      }]
    }

Google Cloud Run
~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Build and push to GCR
    gcloud builds submit --tag gcr.io/PROJECT_ID/py3plex-gui
    
    # Deploy
    gcloud run deploy py3plex-gui \
      --image gcr.io/PROJECT_ID/py3plex-gui \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated \
      --set-env-vars FLASK_ENV=production \
      --set-secrets SECRET_KEY=py3plex-secret:latest

Azure Container Instances
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Create container group
    az container create \
      --resource-group py3plex-rg \
      --name py3plex-gui \
      --image your-registry.azurecr.io/py3plex-gui:latest \
      --dns-name-label py3plex-gui \
      --ports 5000 \
      --environment-variables FLASK_ENV=production \
      --secure-environment-variables SECRET_KEY=$SECRET_KEY

Performance Tuning
------------------

Worker Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Rule of thumb: (2 x CPU cores) + 1
    workers=$((2 * $(nproc) + 1))
    
    gunicorn \
      --workers $workers \
      --threads 2 \
      --worker-class gthread \
      --timeout 120 \
      --bind 0.0.0.0:5000 \
      gui.app:app

Caching
~~~~~~~

Implement caching for expensive operations:

.. code-block:: python

    from flask_caching import Cache
    
    cache = Cache(app, config={'CACHE_TYPE': 'simple'})
    
    @app.route('/api/stats/<network_id>')
    @cache.cached(timeout=300)
    def network_stats(network_id):
        # Expensive computation
        return stats

Database for Persistence
~~~~~~~~~~~~~~~~~~~~~~~~~

For production, consider a database:

.. code-block:: python

    from flask_sqlalchemy import SQLAlchemy
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/py3plex'
    db = SQLAlchemy(app)

Backup and Recovery
-------------------

Automated Backups
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    #!/bin/bash
    # backup.sh
    
    BACKUP_DIR="/backups/py3plex"
    DATE=$(date +%Y%m%d_%H%M%S)
    
    # Backup uploads
    tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" /path/to/uploads
    
    # Backup database (if using one)
    # pg_dump py3plex > "$BACKUP_DIR/db_$DATE.sql"
    
    # Cleanup old backups (keep last 7 days)
    find "$BACKUP_DIR" -type f -mtime +7 -delete

Add to crontab:

.. code-block:: bash

    # Daily backup at 2 AM
    0 2 * * * /path/to/backup.sh

Disaster Recovery
~~~~~~~~~~~~~~~~~

Document recovery procedure:

1. Restore from backup
2. Verify data integrity
3. Restart services
4. Test functionality

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Port already in use:**

.. code-block:: bash

    # Find process using port
    sudo lsof -i :5000
    
    # Kill process
    sudo kill -9 PID

**Permission denied:**

.. code-block:: bash

    # Fix upload directory permissions
    sudo chown -R www-data:www-data /path/to/uploads

**Out of memory:**

.. code-block:: bash

    # Check memory usage
    free -h
    
    # Adjust worker count or add swap

Logs Location
~~~~~~~~~~~~~

* Application logs: ``/var/log/py3plex-gui.log``
* Nginx logs: ``/var/log/nginx/``
* Systemd logs: ``journalctl -u py3plex-gui``

Related Documentation
---------------------

* :doc:`gui_user_guide` - Using the GUI
* :doc:`gui_architecture` - Technical architecture
* :doc:`gui_api_reference` - API endpoints
* :doc:`gui_testing` - Testing the GUI
* :doc:`../deployment/cli_and_docker` - Docker details

**Security Resources:**

* OWASP Flask Security: https://owasp.org/www-project-web-security-testing-guide/
* Flask Security Best Practices: https://flask.palletsprojects.com/en/2.3.x/security/
