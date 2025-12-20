Appendix B: Docker, Docker Compose, and Deployment
==================================================

This appendix provides complete Docker configurations and deployment instructions for py3plex, including the GUI.

Dockerfile Reference
--------------------

Main Dockerfile
~~~~~~~~~~~~~~~

The repository includes a Dockerfile for containerized execution:

.. code-block:: dockerfile

    # File: Dockerfile
    FROM python:3.10-slim
    
    WORKDIR /app
    
    # Install system dependencies
    RUN apt-get update && apt-get install -y \
        git \
        build-essential \
        && rm -rf /var/lib/apt/lists/*
    
    # Copy requirements
    COPY pyproject.toml .
    COPY README.md .
    
    # Install py3plex
    RUN pip install --no-cache-dir -e .
    
    # Copy application code
    COPY py3plex/ ./py3plex/
    COPY examples/ ./examples/
    
    # Set up entry point
    ENTRYPOINT ["python", "-m", "py3plex"]
    CMD ["--help"]

Building the Image
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Build image
    docker build -t py3plex:latest .
    
    # Build with specific Python version
    docker build --build-arg PYTHON_VERSION=3.11 -t py3plex:3.11 .
    
    # Build with version tag matching book release
    docker build -t py3plex:1.0.2 .

Running Containers
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run command
    docker run --rm py3plex:latest --version
    
    # Run analysis script
    docker run --rm py3plex:latest python examples/getting_started/quickstart.py
    
    # Mount data directory
    docker run --rm -v $(pwd)/data:/data py3plex:latest python analysis.py
    
    # Interactive shell
    docker run --rm -it py3plex:latest /bin/bash

Docker Compose
--------------

.. note::
   
   **Docker Compose Command:**
   This book uses the modern ``docker compose`` command (Docker CLI plugin, available since Docker 20.10).
   If you have an older Docker version, you may need to use the legacy ``docker-compose`` command instead.
   The configuration file is always named ``docker-compose.yml`` regardless of which command you use.

GUI Deployment
~~~~~~~~~~~~~~

.. code-block:: yaml

    # File: docker-compose.yml
    version: '3.8'
    
    services:
      gui:
        build:
          context: .
          dockerfile: gui/Dockerfile
        ports:
          - "8000:8000"
        volumes:
          - ./data:/app/data
          - ./uploads:/app/uploads
        environment:
          - ENV=production
          - SECRET_KEY=${SECRET_KEY}
        restart: unless-stopped
      
      # Optional: nginx reverse proxy
      nginx:
        image: nginx:alpine
        ports:
          - "80:80"
          - "443:443"
        volumes:
          - ./nginx.conf:/etc/nginx/nginx.conf:ro
          - ./ssl:/etc/nginx/ssl:ro
        depends_on:
          - gui
        restart: unless-stopped

Running with Docker Compose
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Start services
    docker compose up -d
    
    # View logs
    docker compose logs -f gui
    
    # Stop services
    docker compose down
    
    # Rebuild after changes
    docker compose up -d --build

Controlled Environment Deployment
----------------------------------

.. warning::
   
   The GUI is experimental and not designed for public internet deployment.
   These configurations are provided for deployment in controlled, trusted
   environments (e.g., internal lab networks, behind VPN). They improve
   security but do not make the GUI suitable for untrusted public access.

Security Hardening (Trusted Networks Only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**1. Use environment variables for secrets:**

.. code-block:: bash

    # .env file (DO NOT commit to git)
    SECRET_KEY=your-strong-secret-key-here
    DATABASE_URL=postgresql://user:pass@host/db

.. code-block:: yaml

    # docker-compose.yml
    services:
      gui:
        env_file:
          - .env

**2. Run as non-root user:**

.. code-block:: dockerfile

    # Add to Dockerfile
    RUN useradd -m -u 1000 py3plex
    USER py3plex

**3. Use read-only file systems where possible:**

.. code-block:: yaml

    services:
      gui:
        read_only: true
        tmpfs:
          - /tmp
          - /var/tmp

Nginx Reverse Proxy
~~~~~~~~~~~~~~~~~~~

**nginx.conf:**

.. code-block:: nginx

    events {
        worker_connections 1024;
    }
    
    http {
        upstream gui {
            server gui:8000;
        }
        
        server {
            listen 80;
            server_name yourdomain.com;
            
            # Redirect to HTTPS
            return 301 https://$server_name$request_uri;
        }
        
        server {
            listen 443 ssl;
            server_name yourdomain.com;
            
            ssl_certificate /etc/nginx/ssl/cert.pem;
            ssl_certificate_key /etc/nginx/ssl/key.pem;
            
            # Security headers
            add_header X-Frame-Options "SAMEORIGIN";
            add_header X-Content-Type-Options "nosniff";
            add_header X-XSS-Protection "1; mode=block";
            
            location / {
                proxy_pass http://gui;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }
            
            # File upload limits
            client_max_body_size 100M;
        }
    }

TLS/SSL Configuration
~~~~~~~~~~~~~~~~~~~~~

**Using Let's Encrypt:**

.. code-block:: bash

    # Install certbot
    docker run --rm -v $(pwd)/ssl:/etc/letsencrypt \
        certbot/certbot certonly --standalone \
        -d yourdomain.com \
        --email your@email.com \
        --agree-tos

**Self-signed certificates (development only):**

.. code-block:: bash

    # Generate self-signed certificate
    openssl req -x509 -newkey rsa:4096 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -days 365 -nodes

Authentication Setup
~~~~~~~~~~~~~~~~~~~~

**Basic HTTP authentication (simple):**

.. code-block:: nginx

    server {
        ...
        
        location / {
            auth_basic "Restricted Access";
            auth_basic_user_file /etc/nginx/.htpasswd;
            
            proxy_pass http://gui;
        }
    }

.. code-block:: bash

    # Generate .htpasswd file
    htpasswd -c .htpasswd username

**OAuth2 Proxy (advanced):**

Use ``oauth2-proxy`` as an additional service for integration with GitHub, Google, etc.

Security Checklist
------------------

Before Public Deployment
~~~~~~~~~~~~~~~~~~~~~~~~

- [ ] Use HTTPS (TLS/SSL) for all connections
- [ ] Set strong ``SECRET_KEY`` environment variable
- [ ] Enable authentication (HTTP Basic, OAuth2, etc.)
- [ ] Run containers as non-root user
- [ ] Use read-only file systems where possible
- [ ] Set appropriate file upload limits
- [ ] Enable security headers in nginx
- [ ] Regularly update base images (``docker pull python:3.10-slim``)
- [ ] Monitor logs for suspicious activity
- [ ] Implement rate limiting (via nginx or application)
- [ ] Sanitize user inputs (especially file uploads)
- [ ] Restrict file types for uploads
- [ ] Scan uploaded files for malware
- [ ] Use network isolation (Docker networks)
- [ ] Keep dependencies up to date (``pip install --upgrade``)

Monitoring
~~~~~~~~~~

.. code-block:: yaml

    # Add health checks to docker-compose.yml
    services:
      gui:
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
          interval: 30s
          timeout: 10s
          retries: 3

Cloud Deployment
----------------

AWS Deployment
~~~~~~~~~~~~~~

**Using ECS (Elastic Container Service):**

1. Push image to ECR (Elastic Container Registry)
2. Create ECS task definition
3. Deploy to ECS cluster
4. Use ALB (Application Load Balancer) for routing

**Using EC2:**

1. Launch EC2 instance
2. Install Docker
3. Copy docker-compose.yml to instance
4. Run ``docker compose up -d``

Azure Deployment
~~~~~~~~~~~~~~~~

**Using Azure Container Instances:**

.. code-block:: bash

    az container create \
        --resource-group myResourceGroup \
        --name py3plex-gui \
        --image py3plex:latest \
        --cpu 2 --memory 4 \
        --ports 8000

GCP Deployment
~~~~~~~~~~~~~~

**Using Cloud Run:**

1. Push image to Google Container Registry
2. Deploy to Cloud Run
3. Configure domain and SSL

Performance Tuning
------------------

Container Resource Limits
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    services:
      gui:
        deploy:
          resources:
            limits:
              cpus: '2.0'
              memory: 4G
            reservations:
              cpus: '1.0'
              memory: 2G

Caching
~~~~~~~

Use Docker layer caching to speed up builds:

.. code-block:: dockerfile

    # Install dependencies first (cached layer)
    COPY pyproject.toml .
    RUN pip install -e .
    
    # Copy code second (changes frequently)
    COPY py3plex/ ./py3plex/

Multi-Stage Builds
~~~~~~~~~~~~~~~~~~

For smaller production images:

.. code-block:: dockerfile

    # Build stage
    FROM python:3.10 as builder
    WORKDIR /app
    COPY pyproject.toml .
    RUN pip install --user -e .
    
    # Runtime stage
    FROM python:3.10-slim
    WORKDIR /app
    COPY --from=builder /root/.local /root/.local
    COPY py3plex/ ./py3plex/
    ENV PATH=/root/.local/bin:$PATH

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Issue: Container exits immediately**

Check logs:

.. code-block:: bash

    docker logs <container_id>

**Issue: Permission denied on mounted volumes**

Fix permissions safely by matching container user to host user:

**Method 1: Run container with your user ID (recommended)**

.. code-block:: bash

    docker run --user "$(id -u):$(id -g)" -v $(pwd)/data:/data py3plex-image

**Method 2: Change ownership to match container user**

.. code-block:: bash

    # If container runs as user 1000:1000 (typical)
    sudo chown -R 1000:1000 ./data

**Method 3: Use docker compose with user mapping**

.. code-block:: yaml

    services:
      py3plex:
        user: "${UID}:${GID}"
        volumes:
          - ./data:/data

Then run: ``UID=$(id -u) GID=$(id -g) docker compose up``

.. warning::
   
   **Avoid** ``chmod -R 777 ./data`` as it grants world-writable permissions and 
   creates a security risk. Use user/group mapping instead.

**Issue: Out of memory**

Increase Docker memory limits or container resources.

Summary
-------

This appendix provided:

* Complete Dockerfile and docker-compose.yml examples
* Security hardening guidelines
* Production deployment configurations (nginx, TLS, authentication)
* Cloud deployment options (AWS, Azure, GCP)
* Performance tuning strategies

**Key recommendations for production:**

1. Always use HTTPS
2. Enable authentication
3. Run as non-root
4. Monitor and log
5. Keep dependencies updated
6. Follow security checklist

**See also:** :ref:`gui-chapter` for high-level GUI overview
