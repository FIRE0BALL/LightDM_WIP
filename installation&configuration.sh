#!/bin/bash
# install.sh - Installer for Custom LightDM Python Greeter

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GREETER_NAME="python-greeter"
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/etc/lightdm"
XGREETERS_DIR="/usr/share/xgreeters"
LOG_DIR="/var/log/lightdm"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[*]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Check system compatibility
check_system() {
    print_status "Checking system compatibility..."
    
    # Check if Ubuntu/Debian based
    if ! command -v apt &> /dev/null; then
        print_error "This installer requires apt package manager (Ubuntu/Debian)"
        exit 1
    fi
    
    # Check Ubuntu version
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_status "Detected: $NAME $VERSION"
    fi
    
    # Check if LightDM is installed
    if ! command -v lightdm &> /dev/null; then
        print_warning "LightDM is not installed"
        read -p "Install LightDM? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            apt update && apt install -y lightdm
        else
            print_error "LightDM is required. Exiting."
            exit 1
        fi
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    DEPS=(
        "python3-gi"
        "python3-pam"
        "python3-pip"
        "gir1.2-gtk-3.0"
        "gir1.2-lightdm-1"
        "python3-cairo"
        "python3-gi-cairo"
    )
    
    for dep in "${DEPS[@]}"; do
        if ! dpkg -l | grep -q "^ii  $dep"; then
            print_status "Installing $dep..."
            apt install -y "$dep"
        else
            print_status "$dep already installed"
        fi
    done
    
    # Install Python packages
    print_status "Installing Python packages..."
    pip3 install --upgrade \
        python-pam \
        configparser \
        Pillow
}

# Backup existing configuration
backup_existing() {
    print_status "Backing up existing configuration..."
    
    BACKUP_DIR="/etc/lightdm/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [ -f "$CONFIG_DIR/lightdm.conf" ]; then
        cp "$CONFIG_DIR/lightdm.conf" "$BACKUP_DIR/"
        print_status "Backed up lightdm.conf to $BACKUP_DIR"
    fi
    
    if [ -f "$CONFIG_DIR/lightdm-gtk-greeter.conf" ]; then
        cp "$CONFIG_DIR/lightdm-gtk-greeter.conf" "$BACKUP_DIR/"
    fi
}

# Install greeter files
install_greeter() {
    print_status "Installing greeter files..."
    
    # Copy main greeter script
    if [ -f "greeter.py" ]; then
        cp greeter.py "$INSTALL_DIR/lightdm-python-greeter"
        chmod +x "$INSTALL_DIR/lightdm-python-greeter"
        print_status "Installed greeter to $INSTALL_DIR/lightdm-python-greeter"
    else
        print_error "greeter.py not found in current directory"
        exit 1
    fi
    
    # Copy modules if they exist
    if [ -d "modules" ]; then
        cp -r modules "$INSTALL_DIR/lightdm-python-greeter-modules"
        print_status "Installed modules"
    fi
    
    # Create configuration file
    cat > "$CONFIG_DIR/$GREETER_NAME.conf" << 'EOF'
[Settings]
# Enable/disable auto-submit feature
auto_submit = true

# Delay before validating password (milliseconds)
validation_delay_ms = 300

# Show user list or require manual username entry
show_user_list = true

# Background image path
background = /usr/share/backgrounds/warty-final-ubuntu.png

# Theme: 'dark' or 'light'
theme = dark

# Minimum password length before validation
min_password_length = 4

[Security]
# Maximum login attempts before lockout
max_attempts = 3

# Lockout duration in seconds
lockout_time = 60

# Enable audit logging
enable_audit = true

# Log file path
log_file = /var/log/lightdm/python-greeter.log

[UI]
# Window dimensions
window_width = 400
window_height = 500

# Show session selector
show_session_selector = true

# Show power options
show_power_options = true

# Enable animations
enable_animations = true

# Font settings
font_family = Ubuntu
font_size = 14

[Features]
# Enable face recognition (requires additional setup)
face_recognition = false

# Enable fingerprint (requires fprintd)
fingerprint = false

# Enable virtual keyboard
virtual_keyboard = false

# Enable screen reader support
accessibility = true
EOF
    
    print_status "Created configuration file: $CONFIG_DIR/$GREETER_NAME.conf"
    
    # Create desktop entry for xgreeters
    cat > "$XGREETERS_DIR/$GREETER_NAME.desktop" << EOF
[Desktop Entry]
Name=Python Greeter
Comment=Custom LightDM Python Greeter with Auto-Submit
Exec=$INSTALL_DIR/lightdm-python-greeter
Type=Application
X-Ubuntu-Gettext-Domain=lightdm
EOF
    
    print_status "Created desktop entry: $XGREETERS_DIR/$GREETER_NAME.desktop"
    
    # Create themes directory
    mkdir -p "$CONFIG_DIR/python-greeter-themes"
    
    # Create default theme
    cat > "$CONFIG_DIR/python-greeter-themes/default.css" << 'EOF'
/* Default theme for Python Greeter */
window {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

entry {
    padding: 12px;
    border-radius: 8px;
    border: 2px solid transparent;
    background-color: rgba(255, 255, 255, 0.95);
    font-size: 14px;
    transition: all 0.3s ease;
}

entry:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

button {
    padding: 12px 24px;
    border-radius: 8px;
    border: none;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: bold;
    transition: all 0.3s ease;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

button:active {
    transform: translateY(0);
}

label {
    color: white;
    font-size: 14px;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.error {
    color: #ff6b6b;
    font-weight: bold;
}

.success {
    color: #51cf66;
    font-weight: bold;
}

spinner {
    color: white;
}

checkbutton {
    color: white;
}

combobox {
    padding: 8px;
    border-radius: 8px;
    background-color: rgba(255, 255, 255, 0.95);
}
EOF
    
    print_status "Created default theme"
}

# Configure LightDM to use the new greeter
configure_lightdm() {
    print_status "Configuring LightDM..."
    
    # Update LightDM configuration
    CONFIG_FILE="$CONFIG_DIR/lightdm.conf"
    
    # Check if configuration exists
    if [ ! -f "$CONFIG_FILE" ]; then
        # Create new configuration
        cat > "$CONFIG_FILE" << EOF
[Seat:*]
greeter-session=$GREETER_NAME
user-session=ubuntu
allow-guest=false
EOF
    else
        # Update existing configuration
        if grep -q "^greeter-session=" "$CONFIG_FILE"; then
            sed -i "s/^greeter-session=.*/greeter-session=$GREETER_NAME/" "$CONFIG_FILE"
        else
            echo "greeter-session=$GREETER_NAME" >> "$CONFIG_FILE"
        fi
    fi
    
    print_status "LightDM configured to use $GREETER_NAME"
}

# Create systemd service for additional features
create_systemd_service() {
    print_status "Creating systemd service..."
    
    cat > "/etc/systemd/system/lightdm-python-greeter-helper.service" << EOF
[Unit]
Description=LightDM Python Greeter Helper Service
After=display-manager.service
Wants=display-manager.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/lightdm-python-greeter --helper-mode
Restart=on-failure
User=lightdm
Group=lightdm

[Install]
WantedBy=graphical.target
EOF
    
    systemctl daemon-reload
    systemctl enable lightdm-python-greeter-helper.service
    print_status "Created helper service"
}

# Set up logging
setup_logging() {
    print_status "Setting up logging..."
    
    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Create log file with appropriate permissions
    touch "$LOG_DIR/python-greeter.log"
    chown lightdm:lightdm "$LOG_DIR/python-greeter.log"
    chmod 640 "$LOG_DIR/python-greeter.log"
    
    # Set up log rotation
    cat > "/etc/logrotate.d/lightdm-python-greeter" << EOF
$LOG_DIR/python-greeter.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 640 lightdm lightdm
}
EOF
    
    print_status "Logging configured"
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    # Check if greeter is executable
    if [ -x "$INSTALL_DIR/lightdm-python-greeter" ]; then
        print_status "Greeter is executable"
    else
        print_error "Greeter is not executable"
        return 1
    fi
    
    # Test Python imports
    python3 -c "
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('LightDM', '1')
from gi.repository import Gtk, LightDM
import pam
print('All imports successful')
" 2>/dev/null && print_status "Python dependencies OK" || print_error "Python dependency check failed"
    
    # Test LightDM configuration
    lightdm --show-config 2>/dev/null | grep -q "$GREETER_NAME" && \
        print_status "LightDM configuration OK" || \
        print_warning "LightDM configuration may need manual verification"
}

# Main installation flow
main() {
    clear
    echo "============================================"
    echo "  Custom LightDM Python Greeter Installer  "
    echo "============================================"
    echo
    
    check_root
    check_system
    
    print_warning "This will modify your LightDM configuration."
    read -p "Continue with installation? (y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installation cancelled"
        exit 0
    fi
    
    backup_existing
    install_dependencies
    install_greeter
    configure_lightdm
    create_systemd_service
    setup_logging
    test_installation
    
    echo
    print_status "Installation complete!"
    echo
    echo "Next steps:"
    echo "1. Test the greeter: lightdm --test-mode --debug"
    echo "2. Restart LightDM: systemctl restart lightdm"
    echo "3. Or reboot your system"
    echo
    print_warning "Note: Restarting LightDM will close your current session!"
    echo
    read -p "Restart LightDM now? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl restart lightdm
    else
        print_status "Please restart LightDM manually when ready"
    fi
}

# Run main function
main "$@"