# Dockerfile - Development and testing environment for LightDM Python Greeter
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Metadata
LABEL maintainer="your-email@example.com"
LABEL version="1.0"
LABEL description="LightDM Python Greeter Development Environment"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Core dependencies
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    # LightDM and display server
    lightdm \
    xvfb \
    x11vnc \
    # GTK and GObject dependencies
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-lightdm-1 \
    libgirepository1.0-dev \
    libcairo2-dev \
    # PAM development
    libpam0g-dev \
    libpam-python \
    # Development tools
    git \
    vim \
    curl \
    wget \
    build-essential \
    pkg-config \
    # Testing tools
    dbus-x11 \
    # VNC and remote access
    novnc \
    websockify \
    # Process management
    supervisor \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for development
RUN useradd -m -s /bin/bash developer \
    && usermod -aG sudo developer \
    && echo "developer:developer" | chpasswd

# Set up Python environment
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./

RUN pip3 install --upgrade pip setuptools wheel \
    && pip3 install -r requirements.txt \
    && pip3 install -r requirements-dev.txt

# Copy application code
COPY . /app/

# Set up LightDM configuration for testing
RUN mkdir -p /etc/lightdm/lightdm.conf.d \
    && echo "[Seat:*]" > /etc/lightdm/lightdm.conf.d/50-python-greeter.conf \
    && echo "greeter-session=python-greeter" >> /etc/lightdm/lightdm.conf.d/50-python-greeter.conf \
    && echo "user-session=ubuntu" >> /etc/lightdm/lightdm.conf.d/50-python-greeter.conf

# Install the greeter
RUN cp src/greeter.py /usr/local/bin/lightdm-python-greeter \
    && chmod +x /usr/local/bin/lightdm-python-greeter \
    && cp config/python-greeter.conf /etc/lightdm/ \
    && cp config/python-greeter.desktop /usr/share/xgreeters/

# Set up supervisor configuration
RUN mkdir -p /var/log/supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create startup script
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set up VNC password (changeme)
RUN mkdir -p /root/.vnc \
    && x11vnc -storepasswd changeme /root/.vnc/passwd

# Expose ports
EXPOSE 5900 6080

# Set working directory
WORKDIR /app

# Entry point
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# ===== docker-compose.yml =====
# version: '3.8'
# 
# services:
#   lightdm-greeter:
#     build: .
#     container_name: lightdm-python-greeter
#     privileged: true
#     environment:
#       - DISPLAY=:99
#       - VNC_PASSWORD=changeme
#     ports:
#       - "5900:5900"  # VNC
#       - "6080:6080"  # noVNC web interface
#     volumes:
#       - ./src:/app/src
#       - ./tests:/app/tests
#       - ./config:/app/config
#       - /tmp/.X11-unix:/tmp/.X11-unix
#     networks:
#       - greeter-network
# 
# networks:
#   greeter-network:
#     driver: bridge