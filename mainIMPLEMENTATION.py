#!/usr/bin/env python3
"""
Custom LightDM Python Greeter with Auto-Submit Password Recognition
Author: Your Name
License: MIT
Description: A custom LightDM greeter that automatically submits the password
            once correctly recognized, inspired by Windows login behavior.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('LightDM', '1')

from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
import lightdm
import pam
import threading
import logging
import configparser
import os
import sys
from typing import Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/lightdm/python-greeter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PasswordValidator:
    """Handles real-time password validation using PAM"""
    
    def __init__(self, username: str):
        self.username = username
        self.pam_service = 'lightdm'
        self._validation_thread = None
        self._stop_validation = False
        
    def validate_password_async(self, password: str, callback: Callable[[bool], None]):
        """
        Asynchronously validate password using PAM
        
        Args:
            password: The password to validate
            callback: Function to call with validation result (True/False)
        """
        self._stop_validation = True
        if self._validation_thread and self._validation_thread.is_alive():
            self._validation_thread.join(timeout=0.1)
        
        self._stop_validation = False
        self._validation_thread = threading.Thread(
            target=self._validate_password_thread,
            args=(password, callback),
            daemon=True
        )
        self._validation_thread.start()
    
    def _validate_password_thread(self, password: str, callback: Callable[[bool], None]):
        """Thread worker for password validation"""
        try:
            if self._stop_validation:
                return
                
            # Create PAM authenticator
            p = pam.pam()
            result = p.authenticate(self.username, password, service=self.pam_service)
            
            if not self._stop_validation:
                GLib.idle_add(callback, result)
        except Exception as e:
            logger.error(f"PAM authentication error: {e}")
            if not self._stop_validation:
                GLib.idle_add(callback, False)

class AutoSubmitGreeter(Gtk.Window):
    """Main greeter window with auto-submit password functionality"""
    
    def __init__(self):
        super().__init__(title="Login")
        
        # Initialize LightDM greeter
        self.greeter = lightdm.Greeter()
        self.greeter.connect_to_daemon_sync()
        
        # Load configuration
        self.config = self.load_config()
        
        # Setup window properties
        self.set_default_size(400, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_resizable(False)
        
        # Initialize components
        self.current_user = None
        self.password_validator = None
        self.auto_submit_enabled = self.config.getboolean('Settings', 'auto_submit', fallback=True)
        self.validation_delay = self.config.getint('Settings', 'validation_delay_ms', fallback=300)
        self.validation_timeout = None
        
        # Setup UI
        self.setup_ui()
        
        # Apply theme
        self.apply_theme()
        
        # Handle authentication
        self.greeter.connect("authentication-complete", self.on_authentication_complete)
        self.greeter.connect("show-prompt", self.on_show_prompt)
        
        # Set initial focus
        self.show_all()
        
    def load_config(self) -> configparser.ConfigParser:
        """Load configuration from file"""
        config = configparser.ConfigParser()
        config_path = '/etc/lightdm/python-greeter.conf'
        
        # Default configuration
        config['Settings'] = {
            'auto_submit': 'true',
            'validation_delay_ms': '300',
            'show_user_list': 'true',
            'background': '/usr/share/backgrounds/warty-final-ubuntu.png',
            'theme': 'dark'
        }
        
        if os.path.exists(config_path):
            try:
                config.read(config_path)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        return config
    
    def setup_ui(self):
        """Build the user interface"""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(50)
        main_box.set_margin_bottom(50)
        main_box.set_margin_left(30)
        main_box.set_margin_right(30)
        self.add(main_box)
        
        # Logo/Avatar
        avatar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        avatar_box.set_halign(Gtk.Align.CENTER)
        self.avatar = Gtk.Image()
        self.set_user_avatar()
        avatar_box.pack_start(self.avatar, False, False, 0)
        main_box.pack_start(avatar_box, False, False, 0)
        
        # User selection
        if self.config.getboolean('Settings', 'show_user_list', fallback=True):
            self.user_combo = Gtk.ComboBoxText()
            self.populate_user_list()
            self.user_combo.connect("changed", self.on_user_changed)
            main_box.pack_start(self.user_combo, False, False, 0)
        
        # Username entry (hidden by default if user list is shown)
        self.username_entry = Gtk.Entry()
        self.username_entry.set_placeholder_text("Username")
        self.username_entry.set_halign(Gtk.Align.CENTER)
        self.username_entry.set_size_request(250, -1)
        if not self.config.getboolean('Settings', 'show_user_list', fallback=True):
            main_box.pack_start(self.username_entry, False, False, 0)
        
        # Password entry
        self.password_entry = Gtk.Entry()
        self.password_entry.set_placeholder_text("Password")
        self.password_entry.set_visibility(False)
        self.password_entry.set_halign(Gtk.Align.CENTER)
        self.password_entry.set_size_request(250, -1)
        self.password_entry.connect("changed", self.on_password_changed)
        self.password_entry.connect("activate", self.on_password_activate)
        main_box.pack_start(self.password_entry, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(self.status_label, False, False, 0)
        
        # Progress spinner (for validation feedback)
        self.spinner = Gtk.Spinner()
        self.spinner.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(self.spinner, False, False, 0)
        
        # Auto-submit toggle
        self.auto_submit_check = Gtk.CheckButton(label="Auto-submit password")
        self.auto_submit_check.set_active(self.auto_submit_enabled)
        self.auto_submit_check.set_halign(Gtk.Align.CENTER)
        self.auto_submit_check.connect("toggled", self.on_auto_submit_toggled)
        main_box.pack_start(self.auto_submit_check, False, False, 0)
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)
        
        self.login_button = Gtk.Button(label="Login")
        self.login_button.connect("clicked", self.on_login_clicked)
        button_box.pack_start(self.login_button, False, False, 0)
        
        # Session selector
        self.session_combo = Gtk.ComboBoxText()
        self.populate_session_list()
        button_box.pack_start(self.session_combo, False, False, 0)
        
        # Power menu
        power_button = Gtk.Button(label="⏻")
        power_button.connect("clicked", self.show_power_menu)
        button_box.pack_start(power_button, False, False, 0)
        
        main_box.pack_start(button_box, False, False, 20)
        
    def apply_theme(self):
        """Apply CSS theme to the greeter"""
        css = b"""
        window {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        entry {
            padding: 12px;
            border-radius: 8px;
            border: none;
            background-color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
        }
        
        button {
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            background-color: #4c51bf;
            color: white;
            font-weight: bold;
        }
        
        button:hover {
            background-color: #5a67d8;
        }
        
        label {
            color: white;
            font-size: 14px;
        }
        
        checkbutton {
            color: white;
        }
        
        combobox {
            padding: 8px;
            border-radius: 8px;
            background-color: rgba(255, 255, 255, 0.9);
        }
        
        spinner {
            color: white;
        }
        """
        
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def populate_user_list(self):
        """Populate the user combo box with available users"""
        users = lightdm.UserList().users
        for user in users:
            self.user_combo.append_text(user.name)
        
        # Select first user or last logged in user
        if users:
            self.user_combo.set_active(0)
    
    def populate_session_list(self):
        """Populate the session combo box with available sessions"""
        sessions = lightdm.get_sessions()
        for session in sessions:
            self.session_combo.append_text(session.key)
        
        # Select default session
        if sessions:
            self.session_combo.set_active(0)
    
    def set_user_avatar(self, username: Optional[str] = None):
        """Set the user avatar image"""
        try:
            if username:
                users = lightdm.UserList().users
                for user in users:
                    if user.name == username and user.image:
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                            user.image, 96, 96, True
                        )
                        self.avatar.set_from_pixbuf(pixbuf)
                        return
            
            # Default avatar
            self.avatar.set_from_icon_name("avatar-default", Gtk.IconSize.DIALOG)
            self.avatar.set_pixel_size(96)
        except Exception as e:
            logger.error(f"Failed to set avatar: {e}")
    
    def on_user_changed(self, combo):
        """Handle user selection change"""
        username = combo.get_active_text()
        if username:
            self.current_user = username
            self.set_user_avatar(username)
            self.password_entry.grab_focus()
            
            # Initialize password validator for the selected user
            self.password_validator = PasswordValidator(username)
    
    def on_password_changed(self, entry):
        """Handle password entry change for auto-submit"""
        if not self.auto_submit_enabled:
            return
        
        # Cancel previous validation timeout
        if self.validation_timeout:
            GLib.source_remove(self.validation_timeout)
            self.validation_timeout = None
        
        password = entry.get_text()
        if len(password) < 4:  # Don't validate very short passwords
            return
        
        # Schedule validation after delay
        self.validation_timeout = GLib.timeout_add(
            self.validation_delay,
            self.validate_password_for_auto_submit,
            password
        )
    
    def validate_password_for_auto_submit(self, password: str):
        """Validate password and auto-submit if correct"""
        if not self.password_validator:
            username = self.get_current_username()
            if not username:
                return False
            self.password_validator = PasswordValidator(username)
        
        self.spinner.start()
        self.status_label.set_text("Checking password...")
        
        def validation_callback(is_valid: bool):
            self.spinner.stop()
            if is_valid:
                self.status_label.set_text("Password correct! Logging in...")
                self.perform_login()
            else:
                self.status_label.set_text("")
        
        self.password_validator.validate_password_async(password, validation_callback)
        return False  # Don't repeat timeout
    
    def on_password_activate(self, entry):
        """Handle Enter key press in password field"""
        self.perform_login()
    
    def on_login_clicked(self, button):
        """Handle login button click"""
        self.perform_login()
    
    def on_auto_submit_toggled(self, check_button):
        """Handle auto-submit toggle"""
        self.auto_submit_enabled = check_button.get_active()
    
    def get_current_username(self) -> Optional[str]:
        """Get the current username from UI"""
        if hasattr(self, 'user_combo') and self.user_combo.get_visible():
            return self.user_combo.get_active_text()
        elif self.username_entry.get_visible():
            return self.username_entry.get_text()
        return None
    
    def perform_login(self):
        """Perform the actual login"""
        username = self.get_current_username()
        password = self.password_entry.get_text()
        
        if not username:
            self.status_label.set_text("Please enter username")
            return
        
        if not password:
            self.status_label.set_text("Please enter password")
            return
        
        self.spinner.start()
        self.status_label.set_text("Logging in...")
        
        # Start LightDM authentication
        try:
            self.greeter.authenticate(username)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.spinner.stop()
            self.status_label.set_text("Authentication failed")
    
    def on_show_prompt(self, greeter, text, prompt_type):
        """Handle LightDM prompt"""
        if prompt_type == lightdm.PromptType.SECRET:
            # Provide password to LightDM
            password = self.password_entry.get_text()
            self.greeter.respond(password)
    
    def on_authentication_complete(self, greeter):
        """Handle authentication completion"""
        self.spinner.stop()
        
        if self.greeter.get_is_authenticated():
            # Get selected session
            session = self.session_combo.get_active_text()
            if not session:
                session = None
            
            try:
                # Start session
                self.greeter.start_session_sync(session)
            except Exception as e:
                logger.error(f"Failed to start session: {e}")
                self.status_label.set_text("Failed to start session")
        else:
            self.status_label.set_text("Invalid password")
            self.password_entry.set_text("")
            self.password_entry.grab_focus()
    
    def show_power_menu(self, button):
        """Show power options menu"""
        menu = Gtk.Menu()
        
        if lightdm.get_can_suspend():
            suspend_item = Gtk.MenuItem(label="Suspend")
            suspend_item.connect("activate", lambda x: lightdm.suspend())
            menu.append(suspend_item)
        
        if lightdm.get_can_hibernate():
            hibernate_item = Gtk.MenuItem(label="Hibernate")
            hibernate_item.connect("activate", lambda x: lightdm.hibernate())
            menu.append(hibernate_item)
        
        if lightdm.get_can_restart():
            restart_item = Gtk.MenuItem(label="Restart")
            restart_item.connect("activate", lambda x: lightdm.restart())
            menu.append(restart_item)
        
        if lightdm.get_can_shutdown():
            shutdown_item = Gtk.MenuItem(label="Shutdown")
            shutdown_item.connect("activate", lambda x: lightdm.shutdown())
            menu.append(shutdown_item)
        
        menu.show_all()
        menu.popup_at_widget(button, Gdk.Gravity.SOUTH, Gdk.Gravity.NORTH, None)

def main():
    """Main entry point"""
    try:
        # Create and run greeter
        greeter = AutoSubmitGreeter()
        greeter.connect("destroy", Gtk.main_quit)
        greeter.show_all()
        
        # Hide spinner initially
        greeter.spinner.hide()
        
        Gtk.main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()