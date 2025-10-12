#!/bin/bash
# docker/entrypoint.sh - Docker container entrypoint script

set -e

echo "Starting LightDM Python Greeter Development Environment..."

# Start X virtual framebuffer
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1024x768x24 -nolisten tcp &
sleep 2

# Export display
export DISPLAY=:99

# Start VNC server
echo "Starting VNC server..."
x11vnc -display :99 -bg -nopw -listen localhost -xkb -ncache 10 -forever -passwd ${VNC_PASSWORD:-changeme} &

# Start noVNC web server
echo "Starting noVNC..."
websockify --web=/usr/share/novnc/ 6080 localhost:5900 &

# Wait for services
sleep 2

# Create test user if needed
if ! id -u testuser >/dev/null 2>&1; then
    echo "Creating test user..."
    useradd -m -s /bin/bash testuser
    echo "testuser:password" | chpasswd
fi

# Run any custom initialization
if [ -f "/app/docker/init.sh" ]; then
    echo "Running custom initialization..."
    bash /app/docker/init.sh
fi

# Start LightDM in test mode if TEST_MODE is set
if [ "${TEST_MODE}" = "true" ]; then
    echo "Starting LightDM in test mode..."
    lightdm --test-mode --debug &
fi

echo "Development environment ready!"
echo "Connect via:"
echo "  - VNC: vnc://localhost:5900 (password: ${VNC_PASSWORD:-changeme})"
echo "  - Web: http://localhost:6080/vnc.html"
echo ""

# Execute command passed to docker run
exec "$@"

---

# docker/supervisord.conf - Supervisor configuration for Docker container
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[program:xvfb]
command=/usr/bin/Xvfb :99 -screen 0 1024x768x24 -nolisten tcp
autostart=true
autorestart=true
user=root
priority=1
stdout_logfile=/var/log/supervisor/xvfb.log
stderr_logfile=/var/log/supervisor/xvfb.err.log
environment=DISPLAY=":99"

[program:x11vnc]
command=/usr/bin/x11vnc -display :99 -nopw -listen localhost -xkb -ncache 10 -forever -shared
autostart=true
autorestart=true
user=root
priority=2
stdout_logfile=/var/log/supervisor/x11vnc.log
stderr_logfile=/var/log/supervisor/x11vnc.err.log

[program:novnc]
command=/usr/bin/websockify --web=/usr/share/novnc/ 6080 localhost:5900
autostart=true
autorestart=true
user=root
priority=3
stdout_logfile=/var/log/supervisor/novnc.log
stderr_logfile=/var/log/supervisor/novnc.err.log

[program:lightdm]
command=/usr/sbin/lightdm --test-mode --debug
autostart=false
autorestart=false
user=root
priority=10
stdout_logfile=/var/log/supervisor/lightdm.log
stderr_logfile=/var/log/supervisor/lightdm.err.log
environment=DISPLAY=":99"

[group:display]
programs=xvfb,x11vnc,novnc

---

# docker/init.sh - Custom initialization script
#!/bin/bash

echo "Running custom initialization..."

# Install any additional Python packages for development
if [ -f "/app/requirements-local.txt" ]; then
    pip3 install -r /app/requirements-local.txt
fi

# Set up development environment variables
export PYTHONPATH="/app/src:$PYTHONPATH"
export LIGHTDM_GREETER_DEBUG="1"

# Create necessary directories
mkdir -p /var/log/lightdm
mkdir -p /var/lib/lightdm
mkdir -p /var/cache/lightdm

# Set permissions
chown -R lightdm:lightdm /var/log/lightdm
chown -R lightdm:lightdm /var/lib/lightdm
chown -R lightdm:lightdm /var/cache/lightdm

# Copy test configuration if it exists
if [ -f "/app/config/test-lightdm.conf" ]; then
    cp /app/config/test-lightdm.conf /etc/lightdm/lightdm.conf
fi

echo "Custom initialization complete!"

---

# docker-compose.yml - Docker Compose configuration
version: '3.8'

services:
  lightdm-greeter-dev:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: lightdm-python-greeter-dev
    privileged: true
    environment:
      - DISPLAY=:99
      - VNC_PASSWORD=developer
      - TEST_MODE=false
      - PYTHONPATH=/app/src
      - LIGHTDM_GREETER_DEBUG=1
    ports:
      - "5900:5900"  # VNC
      - "6080:6080"  # noVNC web interface
    volumes:
      - ./src:/app/src:ro
      - ./tests:/app/tests:ro
      - ./config:/app/config:ro
      - ./logs:/var/log/lightdm
      - /tmp/.X11-unix:/tmp/.X11-unix
    networks:
      - greeter-network
    healthcheck:
      test: ["CMD", "pgrep", "Xvfb"]
      interval: 30s
      timeout: 10s
      retries: 3

  lightdm-greeter-test:
    build:
      context: .
      dockerfile: Dockerfile
      target: test
    container_name: lightdm-python-greeter-test
    privileged: true
    environment:
      - DISPLAY=:99
      - TEST_MODE=true
      - CI=true
    volumes:
      - ./src:/app/src:ro
      - ./tests:/app/tests:ro
      - ./coverage:/app/coverage
    networks:
      - greeter-network
    command: ["pytest", "tests/", "--cov=src", "--cov-report=html:/app/coverage"]

networks:
  greeter-network:
    driver: bridge

volumes:
  logs:
  coverage:

---

# Makefile - Development automation
.PHONY: help build run test clean logs shell vnc stop

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker container
	docker-compose build lightdm-greeter-dev

run: ## Run development container
	docker-compose up -d lightdm-greeter-dev
	@echo "Development environment starting..."
	@echo "VNC: vnc://localhost:5900 (password: developer)"
	@echo "Web: http://localhost:6080/vnc.html"

test: ## Run tests in container
	docker-compose run --rm lightdm-greeter-test

clean: ## Clean up containers and volumes
	docker-compose down -v
	rm -rf logs/* coverage/*

logs: ## View container logs
	docker-compose logs -f lightdm-greeter-dev

shell: ## Open shell in container
	docker-compose exec lightdm-greeter-dev /bin/bash

vnc: ## Open VNC viewer
	vncviewer localhost:5900 || xdg-open vnc://localhost:5900

stop: ## Stop all containers
	docker-compose down

install-local: ## Install for local development
	pip install -e .[dev]
	pre-commit install

format: ## Format code
	black src/ tests/
	isort src/ tests/

lint: ## Run linters
	flake8 src/ tests/
	pylint src/
	mypy src/

coverage: ## Generate coverage report
	pytest tests/ --cov=src --cov-report=html
	xdg-open htmlcov/index.html

docs: ## Build documentation
	cd docs && make html
	xdg-open docs/_build/html/index.html