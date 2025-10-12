# 🔐 Custom LightDM Python Greeter with Auto-Submit Password Recognition

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-20.04%2B-orange)](https://ubuntu.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

A custom LightDM greeter for Ubuntu that brings Windows-like login convenience by automatically submitting passwords once correctly typed - no Enter key required! Built with Python, GTK, and PAM integration for a seamless and secure login experience.

## ✨ Features

- **Auto-Submit Password**: Automatically logs in once the correct password is detected
- **Real-time Validation**: Validates passwords as you type using PAM
- **Beautiful UI**: Modern, customizable interface with gradient backgrounds
- **Session Selection**: Choose between different desktop environments
- **User Management**: Visual user list with avatar support
- **Power Options**: Integrated shutdown, restart, suspend, and hibernate
- **Security First**: Built on PAM for robust authentication
- **Configurable**: Extensive configuration options via config file
- **Accessibility**: Reduces required keystrokes for users with mobility impairments

## 🎥 Demo

![Greeter Demo](docs/demo.gif)

## 🚀 Installation

### Prerequisites

```bash
# Install required packages
sudo apt update
sudo apt install -y \
    lightdm \
    python3-gi \
    python3-pam \
    python3-pip \
    gir1.2-gtk-3.0 \
    gir1.2-lightdm-1
```

### Install the Greeter

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/lightdm-python-greeter.git
cd lightdm-python-greeter
```

2. **Run the installer:**
```bash
sudo ./install.sh
```

Or manually:

```bash
# Copy greeter files
sudo cp greeter.py /usr/local/bin/lightdm-python-greeter
sudo chmod +x /usr/local/bin/lightdm-python-greeter

# Copy configuration
sudo cp config/python-greeter.conf /etc/lightdm/
sudo cp config/python-greeter.desktop /usr/share/xgreeters/

# Set as default greeter
sudo nano /etc/lightdm/lightdm.conf
# Add: greeter-session=python-greeter
```

3. **Test the greeter:**
```bash
lightdm --test-mode --debug
```

4. **Restart LightDM:**
```bash
sudo systemctl restart lightdm
```

## ⚙️ Configuration

Edit `/etc/lightdm/python-greeter.conf`:

```ini
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

[Security]
# Minimum password length before validation
min_password_length = 4

# Enable password strength indicator
show_strength_indicator = false

# Lock after failed attempts
max_attempts = 3
lockout_time = 60

[UI]
# Window dimensions
window_width = 400
window_height = 500

# Show session selector
show_session_selector = true

# Show power options
show_power_options = true

# Custom CSS file
custom_css = /etc/lightdm/python-greeter.css
```

## 🛠️ Development

### Project Structure

```
lightdm-python-greeter/
├── greeter.py              # Main greeter implementation
├── install.sh              # Installation script
├── uninstall.sh           # Uninstallation script
├── config/
│   ├── python-greeter.conf     # Default configuration
│   ├── python-greeter.desktop   # Desktop entry for LightDM
│   └── python-greeter.css       # Custom CSS themes
├── modules/
│   ├── __init__.py
│   ├── validator.py        # PAM validation module
│   ├── ui_builder.py      # UI construction helpers
│   ├── config_manager.py  # Configuration handling
│   └── security.py        # Security utilities
├── themes/
│   ├── default.css
│   ├── dark.css
│   └── light.css
├── tests/
│   ├── test_validator.py
│   ├── test_ui.py
│   └── test_security.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── SECURITY.md
└── README.md
```

### Building from Source

```bash
# Install development dependencies
pip3 install -r requirements-dev.txt

# Run tests
python3 -m pytest tests/

# Run linting
flake8 greeter.py modules/
pylint greeter.py modules/

# Build package
python3 setup.py sdist bdist_wheel
```

### Testing in Docker

```bash
# Build Docker image with LightDM environment
docker build -t lightdm-greeter-test .

# Run container with X11 forwarding
docker run -it \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    lightdm-greeter-test
```

## 🔧 Improvements Roadmap

### Phase 1: Core Enhancements (Current)
- [ ] Add biometric authentication support (fingerprint/face recognition)
- [ ] Implement password strength meter with visual feedback
- [ ] Add multi-monitor support with proper scaling
- [ ] Create animated transitions between states
- [ ] Add sound effects for login events

### Phase 2: Security & Performance
- [ ] Implement rate limiting for validation attempts
- [ ] Add brute-force protection with exponential backoff
- [ ] Cache validated passwords securely in memory
- [ ] Optimize PAM calls with connection pooling
- [ ] Add support for 2FA/MFA authentication

### Phase 3: User Experience
- [ ] Add customizable themes with theme editor
- [ ] Implement user preference persistence
- [ ] Add keyboard shortcuts for power users
- [ ] Create accessibility features (screen reader support, high contrast)
- [ ] Add internationalization (i18n) support

### Phase 4: Advanced Features
- [ ] WebAuthn/FIDO2 support for passwordless login
- [ ] Remote login capabilities
- [ ] Guest session management
- [ ] Integration with LDAP/Active Directory
- [ ] Plugin system for custom authentication methods

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add unit tests for new features
- Update documentation as needed
- Ensure backward compatibility
- Test on multiple Ubuntu versions

## ⚠️ Security Considerations

**Important:** While this greeter enhances convenience, consider these security implications:

1. **Auto-submit Risk**: On shared computers, auto-submit could allow unauthorized access if someone watches you type
2. **Timing Attacks**: Real-time validation might leak password length information
3. **Memory Security**: Passwords are temporarily stored in memory during validation
4. **PAM Integration**: Ensure PAM modules are properly configured for your security requirements

**Recommended Use Cases:**
- Personal computers with physical security
- Controlled kiosk environments
- Development/testing machines
- Accessibility-focused deployments

**NOT Recommended for:**
- Public computers
- High-security environments
- Shared workstations without user isolation

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Security Model](docs/SECURITY.md)
- [Theming Guide](docs/THEMING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 🐛 Troubleshooting

### Common Issues

**Greeter doesn't start:**
```bash
# Check LightDM logs
sudo journalctl -u lightdm -f

# Verify greeter installation
ls -la /usr/local/bin/lightdm-python-greeter

# Test in debug mode
sudo lightdm --test-mode --debug
```

**Auto-submit not working:**
- Check if PAM is properly configured
- Verify user has necessary permissions
- Check configuration file settings
- Review logs at `/var/log/lightdm/python-greeter.log`

**UI issues:**
- Ensure GTK3 and PyGObject are installed
- Check for missing Python dependencies
- Verify X11/Wayland session is running

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- LightDM developers for the excellent display manager
- Ubuntu community for testing and feedback
- PAM project for secure authentication framework
- Contributors and testers

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/lightdm-python-greeter?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/lightdm-python-greeter?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/lightdm-python-greeter)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/lightdm-python-greeter)

## 🔗 Links

- [Project Website](https://your-project-site.com)
- [Bug Reports](https://github.com/yourusername/lightdm-python-greeter/issues)
- [Feature Requests](https://github.com/yourusername/lightdm-python-greeter/issues)
- [Wiki](https://github.com/yourusername/lightdm-python-greeter/wiki)

---

<p align="center">Made with ❤️ for the Ubuntu community</p>
<p align="center">⭐ Star us on GitHub — it helps!</p>