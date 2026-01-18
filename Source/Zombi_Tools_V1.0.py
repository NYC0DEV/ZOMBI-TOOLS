import sys
import subprocess
import os
import time

# ==============================================================================
# AUTO-INSTALL DEPENDENCIES FIRST
# ==============================================================================
print("Checking dependencies...")
PACKAGES = ['pymem', 'keyboard', 'psutil', 'pyautogui', 'pillow', 'pynput']
for package in PACKAGES:
    try:
        if package == 'pillow':
            __import__('PIL')
        else:
            __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
        print(f"✓ {package} installed")

print("✓ All dependencies ready\n")

# ==============================================================================
# AUTO-ELEVATE TO ADMIN (Required for keyboard/mouse control)
# ==============================================================================
def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell.IsUserAnAdmin()
    except:
        return False

def elevate_to_admin():
    try:
        import ctypes
        if not is_admin():
            print("Requesting admin privileges...")
            ctypes.windll.shell.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
    except:
        pass

# Elevate to admin NOW
elevate_to_admin()

# Now import everything
import tkinter as tk
from tkinter import ttk
from threading import Thread
import itertools
import math
import io

# ==============================================================================
# FINAL DEPENDENCY CHECK
# ==============================================================================
try:
    import ctypes
    import pymem
    import pymem.process
    import keyboard
    import psutil
    import pyautogui
    from PIL import Image, ImageDraw, ImageTk
    from pynput import mouse
except ImportError as e:
    print(f"Error: {e}")
    sys.exit()

# ==============================================================================
# MAIN LOGIC ENGINE
# ==============================================================================
class ZombiUTrainer:
    def __init__(self):
        # Get the ACTUAL app folder (where the .py file is)
        self.app_folder = os.path.dirname(os.path.abspath(__file__))
        
        # Print app folder at startup
        print(f"\n{'='*80}")
        print(f"APP FOLDER: {self.app_folder}")
        print(f"{'='*80}\n")
        
        # FIX FOLDER PERMISSIONS - Make folder writable
        self.fix_folder_permissions()
        
        self.pm = None
        self.process_found = False
        self.running = True
        self.status = "Waiting for ZombiU..."
        self.process_name = None
        
        # Possible ZombiU process names
        self.game_processes = [
            "ZombiU.exe", "ZOMBIU.exe", "zombiu.exe",
            "ZombieU.exe", "Zombi.exe", "ZOMBI.exe", "zombi.exe",
            "ZombiU_PC.exe", "ZombiUbisoft.exe"
        ]
        
        # F1: Keypad Solver
        self.keypad_active = False
        self.keypad_solving = False
        self.keypad_code = ""
        self.keypad_method = "auto"
        self.found_codes = []
        self.manual_code_entry = ""
        self.last_successful_code = ""
        self.keypad_save_file = os.path.join(self.app_folder, "keypad_resume.txt")  # App folder
        self.load_keypad_resume()
        self.circle_positions = []
        self.circle_ready = False
        self.auto_clicking = False
        
        # F2: Key Blocker
        self.key_blocker_active = False
        self.blocked_keys = set()
        self.available_keys = ['shift', 'f', 'tab', 'w', 'r', 'space']  # Preset button keys
        self.last_added_key = None
        self.key_add_time = 0
        self.custom_keys_enabled = True  # Controls if custom keys actually block
        self.keys_save_file = os.path.join(self.app_folder, "keys.txt")  # App folder
        self.load_blocked_keys()
        
        # F3: Timer
        self.timer_active = False
        self.timer_paused = False
        self.timer_start = 0
        self.timer_elapsed = 0
        
        # Crosshair Settings
        self.crosshair_enabled = False
        self.crosshair_size = 20
        self.crosshair_color = '#00ff00'
        self.crosshair_shape = 'circle'
        self.crosshair_x = None
        self.crosshair_y = None
        self.crosshair_locked = True
        self.crosshair_width = 2  # Line thickness/boldness
        self.taskbar_visible = True  # Default: Windows taskbar ON (default state)
        self.fullscreen_enabled = False  # Default: fullscreen OFF
        
        # Speed settings (adjustable)
        self.click_delay = 0.02  # 20ms - ULTRA ULTRA FAST clicking
        self.enter_delay = 0.02  # 20ms - ULTRA ULTRA FAST enter key
        
        # HUD customization settings
        self.hud_bg_color = '#000000'
        self.hud_text_color = '#00ff00'
        self.hud_border_color = '#00ff00'
        self.overlay_opacity = 0.15
        self.hud_theme = 'default'
        self.hud_corner_radius = 0
        self.hud_border_width = 2
        
        # Sound settings
        self.sound_enabled = True
        self.beep_countdown = True
        
        # Autostart Timer settings
        self.autostart_timer_delay = 10  # seconds
        self.autostart_timer_enabled = True
        self.autostart_timer_running = False
        self.autostart_timer_start_time = 0
        
        # Keybind settings (F2 REMOVED)
        self.keybind_f1 = 0x70  # F1
        self.keybind_f3 = 0x72  # F3
        self.keybind_f4 = 0x73  # F4
        
        # Developer Settings (DEFAULT OFF)
        self.dev_mode = False
        self.dev_logs = False
        self.dev_show_fps = False
        self.dev_show_mouse_pos = False
        self.dev_show_hotkey_debug = False
        
        # Fullscreen overlay settings (for when ZombiU is fullscreen)
        self.dev_always_on_top = True  # Keep window on top of fullscreen games
        self.dev_window_transparency = 0.95  # Transparency when behind fullscreen
        
        # CREATE ALL FILES ON STARTUP if they don't exist
        try:
            settings_path = os.path.join(self.app_folder, 'settings.txt')
            keypad_path = os.path.join(self.app_folder, 'keypad_resume.txt')
            keys_path = os.path.join(self.app_folder, 'keys.txt')
            
            # Verify app folder is writable
            if not os.access(self.app_folder, os.W_OK):
                print(f"WARNING: App folder not writable: {self.app_folder}")
                print("Trying to fix permissions...")
                try:
                    os.chmod(self.app_folder, 0o777)
                except Exception as e:
                    print(f"ERROR: Could not fix folder permissions: {e}")
            
            # Create settings.txt
            if not os.path.exists(settings_path):
                try:
                    self.create_default_settings()
                except Exception as e:
                    print(f"ERROR creating settings.txt: {e}")
                    self.status = f"Error creating settings.txt: {e}"
            
            # Create keypad_resume.txt
            if not os.path.exists(keypad_path):
                try:
                    with open(keypad_path, 'w') as f:
                        f.write("# Keypad Resume\n")
                    os.chmod(keypad_path, 0o666)
                except Exception as e:
                    print(f"ERROR creating keypad_resume.txt: {e}")
            
            # Create keys.txt
            if not os.path.exists(keys_path):
                try:
                    with open(keys_path, 'w') as f:
                        f.write("# Blocked Keys\n")
                    os.chmod(keys_path, 0o666)
                except Exception as e:
                    print(f"ERROR creating keys.txt: {e}")
        except Exception as e:
            print(f"FATAL ERROR in file creation: {e}")
            self.status = f"Error creating files: {e}"
        
        # Now load settings
        self.load_settings()
    
    def load_settings(self):
        """Load settings from settings.txt file - auto-recreate if missing/corrupted"""
        try:
            settings_path = os.path.join(self.app_folder, 'settings.txt')
            
            # Check if file exists AND has content
            file_exists = os.path.exists(settings_path)
            file_has_content = False
            
            if file_exists:
                try:
                    file_size = os.path.getsize(settings_path)
                    file_has_content = file_size > 0
                except:
                    file_has_content = False
            
            # If file is missing or empty, recreate it
            if not file_exists or not file_has_content:
                self.create_default_settings()
                return  # Load defaults, don't try to read
            
            # File exists and has content - try to load it
            try:
                with open(settings_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                if key == 'click_delay':
                                    self.click_delay = float(value)
                                elif key == 'enter_delay':
                                    self.enter_delay = float(value)
                                elif key == 'hud_bg_color':
                                    self.hud_bg_color = value
                                elif key == 'hud_text_color':
                                    self.hud_text_color = value
                                elif key == 'hud_border_color':
                                    self.hud_border_color = value
                                elif key == 'hud_theme':
                                    self.hud_theme = value
                                elif key == 'hud_corner_radius':
                                    self.hud_corner_radius = int(value)
                                elif key == 'hud_border_width':
                                    self.hud_border_width = int(value)
                                elif key == 'overlay_opacity':
                                    self.overlay_opacity = float(value)
                                elif key == 'sound_enabled':
                                    self.sound_enabled = value.lower() == 'true'
                                elif key == 'beep_countdown':
                                    self.beep_countdown = value.lower() == 'true'
                                elif key == 'autostart_timer_delay':
                                    self.autostart_timer_delay = int(value)
                                elif key == 'autostart_timer_enabled':
                                    self.autostart_timer_enabled = value.lower() == 'true'
                                elif key == 'keybind_f1':
                                    self.keybind_f1 = int(value, 16)
                                elif key == 'keybind_f3':
                                    self.keybind_f3 = int(value, 16)
                                elif key == 'keybind_f4':
                                    self.keybind_f4 = int(value, 16)
                                elif key == 'dev_mode':
                                    self.dev_mode = value.lower() == 'true'
                                elif key == 'dev_logs':
                                    self.dev_logs = value.lower() == 'true'
                                elif key == 'dev_show_fps':
                                    self.dev_show_fps = value.lower() == 'true'
                                elif key == 'dev_show_mouse_pos':
                                    self.dev_show_mouse_pos = value.lower() == 'true'
                                elif key == 'dev_show_hotkey_debug':
                                    self.dev_show_hotkey_debug = value.lower() == 'true'
                                elif key == 'dev_always_on_top':
                                    self.dev_always_on_top = value.lower() == 'true'
                                elif key == 'dev_window_transparency':
                                    self.dev_window_transparency = float(value)
                                elif key == 'fullscreen_enabled':
                                    self.fullscreen_enabled = value.lower() == 'true'
                                elif key == 'taskbar_visible':
                                    self.taskbar_visible = value.lower() == 'true'
                
                self.apply_hud_theme()
            except Exception as e:
                # If file corrupted, recreate it
                self.create_default_settings()
        except Exception as e:
            self.status = f"Error loading settings: {e}"
            self.create_default_settings()
    
    def apply_hud_theme(self):
        if self.hud_theme == 'military':
            self.hud_bg_color = '#1a1a00'
            self.hud_text_color = '#88ff00'
            self.hud_border_color = '#556b2f'
            self.hud_border_width = 3
            self.hud_corner_radius = 0
        elif self.hud_theme == 'alpha':
            self.hud_bg_color = '#0a0a0a'
            self.hud_text_color = '#00ffff'
            self.hud_border_color = '#0080ff'
            self.hud_border_width = 1
            self.hud_corner_radius = 0
        elif self.hud_theme == 'rounded':
            self.hud_bg_color = '#000000'
            self.hud_text_color = '#00ff00'
            self.hud_border_color = '#00ff00'
            self.hud_corner_radius = 15
            self.hud_border_width = 2
        elif self.hud_theme == 'minimal':
            self.hud_bg_color = '#000000'
            self.hud_text_color = '#ffffff'
            self.hud_border_color = '#333333'
            self.hud_border_width = 1
            self.hud_corner_radius = 0
        elif self.hud_theme == 'modern2026':
            # Modern 2026 look - Clean, sleek, rounded corners
            self.hud_bg_color = '#0f0f12'  # Deep dark with slight blue tint
            self.hud_text_color = '#e0e0e0'  # Clean light gray
            self.hud_border_color = '#00d4ff'  # Bright cyan accent
            self.hud_border_width = 2  # Slightly thicker for modern look
            self.hud_corner_radius = 12  # Smooth rounded corners
        else:  # default theme
            self.hud_bg_color = '#000000'
            self.hud_text_color = '#00ff00'
            self.hud_border_color = '#00ff00'
            self.hud_border_width = 2
            self.hud_corner_radius = 0
    
    def create_default_settings(self):
        """Create default settings.txt file with error handling"""
        try:
            settings_path = os.path.join(self.app_folder, 'settings.txt')
            
            # Ensure we can write to the file
            try:
                # Try to open and write
                with open(settings_path, 'w') as f:
                    f.write("# Zombi Tools Settings v1.0\n")
                    f.write("# Updated: 2026\n\n")
                    
                    f.write("# SPEED SETTINGS\n")
                    f.write("click_delay=0.02\n")
                    f.write("enter_delay=0.02\n\n")
                    
                    f.write("# HUD THEME (default, military, alpha, rounded, minimal, modern2026)\n")
                    f.write("hud_theme=default\n")
                    f.write("hud_bg_color=#000000\n")
                    f.write("hud_text_color=#00ff00\n")
                    f.write("hud_border_color=#00ff00\n")
                    f.write("hud_corner_radius=0\n")
                    f.write("hud_border_width=2\n\n")
                    
                    f.write("# MODERN 2026 THEME (Uncomment to use - Clean & Sleek)\n")
                    f.write("# hud_theme=modern2026\n")
                    f.write("# hud_bg_color=#0f0f12\n")
                    f.write("# hud_text_color=#e0e0e0\n")
                    f.write("# hud_border_color=#00d4ff\n")
                    f.write("# hud_corner_radius=12\n")
                    f.write("# hud_border_width=2\n\n")
                    
                    f.write("# OVERLAY SETTINGS\n")
                    f.write("overlay_opacity=0.15\n\n")
                    
                    f.write("# SOUND SETTINGS\n")
                    f.write("sound_enabled=true\n")
                    f.write("beep_countdown=true\n\n")
                    
                    f.write("# TIMER SETTINGS\n")
                    f.write("autostart_timer_delay=10\n")
                    f.write("autostart_timer_enabled=true\n\n")
                    
                    f.write("# KEYBINDS\n")
                    f.write("keybind_f1=0x70\n")
                    f.write("keybind_f3=0x72\n")
                    f.write("keybind_f4=0x73\n\n")
                    
                    f.write("# WINDOW SETTINGS\n")
                    f.write("fullscreen_enabled=false\n")
                    f.write("taskbar_visible=true\n\n")
                    
                    f.write("# DEVELOPER SETTINGS (DEFAULT: ALL OFF)\n")
                    f.write("dev_mode=false\n")
                    f.write("dev_logs=false\n")
                    f.write("dev_show_fps=false\n")
                    f.write("dev_show_mouse_pos=false\n")
                    f.write("dev_show_hotkey_debug=false\n")
                    f.write("dev_always_on_top=true\n")
                    f.write("dev_window_transparency=0.95\n\n")
            except PermissionError:
                print(f"ERROR: Permission denied writing to {settings_path}")
                print(f"Trying alternate location...")
                # Try alternate temp location
                import tempfile
                temp_dir = tempfile.gettempdir()
                alt_path = os.path.join(temp_dir, 'zombi_settings.txt')
                with open(alt_path, 'w') as f:
                    f.write("# Zombi Tools Settings v4.0\n")
                    # ... write settings
                print(f"Settings saved to: {alt_path}")
                self.status = f"Settings saved to temp folder: {alt_path}"
                return
            
            # FIX PERMISSIONS - Make file writable
            try:
                os.chmod(settings_path, 0o666)
            except Exception as e:
                print(f"WARNING: Could not set file permissions: {e}")
            
            self.status = f"✓ Settings.txt created: {settings_path}"
            print(f"Created settings.txt at: {settings_path}")
        except Exception as e:
            print(f"FATAL ERROR creating settings: {e}")
            self.status = f"Error creating settings: {e}"
    
    def load_keypad_resume(self):
        """Load last codes from notepad file"""
        try:
            if os.path.exists(self.keypad_save_file):
                with open(self.keypad_save_file, 'r') as f:
                    data = f.read().strip()
                    if data:
                        lines = data.split('\n')
                        self.found_codes = []
                        loaded_count = 0
                        for line in lines:
                            line = line.strip()
                            if line.startswith('LAST:'):
                                # Load last tried code
                                self.keypad_code = line.replace('LAST:', '')
                            elif line:
                                # Load found codes (only last 10)
                                self.found_codes.append((line, "Resumed"))
                                loaded_count += 1
                        if loaded_count > 0:
                            self.status = f"Loaded {loaded_count} recent codes"
            else:
                # Create empty file if it doesn't exist
                with open(self.keypad_save_file, 'w') as f:
                    f.write("")
                # Set file permissions
                try:
                    os.chmod(self.keypad_save_file, 0o666)
                except:
                    pass
        except Exception as e:
            pass
    
    def load_blocked_keys(self):
        """Load blocked keys from keys.txt file"""
        try:
            keys_path = os.path.join(self.app_folder, self.keys_save_file)
            if os.path.exists(keys_path):
                with open(keys_path, 'r') as f:
                    data = f.read().strip()
                    if data and data != "# Blocked Keys":
                        keys = data.split(',')
                        self.blocked_keys = set(k.strip().lower() for k in keys if k.strip())
                        if self.blocked_keys:
                            self.status = f"Loaded {len(self.blocked_keys)} blocked keys"
        except Exception as e:
            pass  # Silent fail
    
    def save_blocked_keys(self):
        """Save blocked keys to keys.txt file with verification"""
        try:
            keys_path = os.path.join(self.app_folder, self.keys_save_file)
            
            # Create backup before overwriting
            backup_file = keys_path + '.bak'
            if os.path.exists(keys_path):
                try:
                    import shutil
                    shutil.copy2(keys_path, backup_file)
                except:
                    pass
            
            # Atomic write - write to temp file first
            temp_file = keys_path + '.tmp'
            
            with open(temp_file, 'w') as f:
                f.write(','.join(sorted(self.blocked_keys)))
                f.flush()
                try:
                    os.fsync(f.fileno())
                except:
                    pass
            
            # Verify temp file was written
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                # Move temp to actual file (atomic operation)
                try:
                    import shutil
                    shutil.move(temp_file, keys_path)
                except:
                    # Fallback: copy content
                    with open(temp_file, 'r') as src:
                        with open(keys_path, 'w') as dst:
                            dst.write(src.read())
                    try:
                        os.remove(temp_file)
                    except:
                        pass
            
            try:
                os.chmod(keys_path, 0o666)
            except:
                pass
        except Exception as e:
            print(f"DEBUG: Failed to save blocked keys: {e}")
    
    def save_taskbar_state(self):
        """Save taskbar visibility state to settings.txt"""
        try:
            settings_path = os.path.join(self.app_folder, 'settings.txt')
            # Read current settings
            settings = {}
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                settings[key.strip()] = value.strip()
            
            # Update taskbar state
            settings['taskbar_visible'] = 'true' if self.taskbar_visible else 'false'
            
            # Write back to settings
            with open(settings_path, 'w') as f:
                f.write("# Zombi Tools Settings v1.0\n")
                f.write("# Updated: 2026\n\n")
                
                f.write("# SPEED SETTINGS\n")
                f.write(f"click_delay={settings.get('click_delay', '0.02')}\n")
                f.write(f"enter_delay={settings.get('enter_delay', '0.02')}\n\n")
                
                f.write("# HUD THEME (default, military, alpha, rounded, minimal, modern2026)\n")
                f.write(f"hud_theme={settings.get('hud_theme', 'default')}\n")
                f.write(f"hud_bg_color={settings.get('hud_bg_color', '#000000')}\n")
                f.write(f"hud_text_color={settings.get('hud_text_color', '#00ff00')}\n")
                f.write(f"hud_border_color={settings.get('hud_border_color', '#00ff00')}\n")
                f.write(f"hud_corner_radius={settings.get('hud_corner_radius', '0')}\n")
                f.write(f"hud_border_width={settings.get('hud_border_width', '2')}\n\n")
                
                f.write("# OVERLAY SETTINGS\n")
                f.write(f"overlay_opacity={settings.get('overlay_opacity', '0.15')}\n\n")
                
                f.write("# SOUND SETTINGS\n")
                f.write(f"sound_enabled={settings.get('sound_enabled', 'true')}\n")
                f.write(f"beep_countdown={settings.get('beep_countdown', 'true')}\n\n")
                
                f.write("# TIMER SETTINGS\n")
                f.write(f"autostart_timer_delay={settings.get('autostart_timer_delay', '10')}\n")
                f.write(f"autostart_timer_enabled={settings.get('autostart_timer_enabled', 'true')}\n\n")
                
                f.write("# KEYBINDS\n")
                f.write(f"keybind_f1={settings.get('keybind_f1', '0x70')}\n")
                f.write(f"keybind_f3={settings.get('keybind_f3', '0x72')}\n")
                f.write(f"keybind_f4={settings.get('keybind_f4', '0x73')}\n\n")
                
                f.write("# WINDOW SETTINGS\n")
                f.write(f"fullscreen_enabled={settings.get('fullscreen_enabled', 'false')}\n")
                f.write(f"taskbar_visible={settings['taskbar_visible']}\n\n")
                
                f.write("# DEVELOPER SETTINGS (DEFAULT: ALL OFF)\n")
                f.write(f"dev_mode={settings.get('dev_mode', 'false')}\n")
                f.write(f"dev_logs={settings.get('dev_logs', 'false')}\n")
                f.write(f"dev_show_fps={settings.get('dev_show_fps', 'false')}\n")
                f.write(f"dev_show_mouse_pos={settings.get('dev_show_mouse_pos', 'false')}\n")
                f.write(f"dev_show_hotkey_debug={settings.get('dev_show_hotkey_debug', 'false')}\n")
        except Exception as e:
            pass
    
    def save_keypad_resume(self):
        """Save ALL codes to notepad file but keep memory optimized"""
        try:
            # Create backup before overwriting
            backup_file = self.keypad_save_file + '.bak'
            if os.path.exists(self.keypad_save_file):
                try:
                    import shutil
                    shutil.copy2(self.keypad_save_file, backup_file)
                except:
                    pass
            
            # Atomic write - write to temp file first
            temp_file = self.keypad_save_file + '.tmp'
            
            with open(temp_file, 'w') as f:
                # Save ALL found codes to notepad
                for code_tuple in self.found_codes:
                    if code_tuple and code_tuple[0]:
                        f.write(code_tuple[0] + '\n')
                
                # Save current/last keypad code on a separate line with marker
                if self.keypad_code:
                    f.write(f"LAST:{self.keypad_code}\n")
                
                # Force flush before close
                f.flush()
                try:
                    os.fsync(f.fileno())
                except:
                    pass
            
            # Verify temp file was written
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                # Move temp to actual file (atomic operation)
                try:
                    import shutil
                    shutil.move(temp_file, self.keypad_save_file)
                except:
                    # Fallback: copy content
                    with open(temp_file, 'r') as src:
                        with open(self.keypad_save_file, 'w') as dst:
                            dst.write(src.read())
                    try:
                        os.remove(temp_file)
                    except:
                        pass
            
            # Ensure file is writable and not read-only
            try:
                os.chmod(self.keypad_save_file, 0o666)
            except:
                pass
            
            # Keep found_codes limited in memory to prevent crash (but ALL saved to file)
            # Keep only last 10 codes in memory for GUI display
            if len(self.found_codes) > 10:
                self.found_codes = self.found_codes[-10:]
        except Exception as e:
            self.status = f"ERROR saving resume: {e}"
            print(f"DEBUG: Failed to save keypad resume: {e}")
    
    def reset_keypad_resume(self):
        """Delete the resume file"""
        try:
            if os.path.exists(self.keypad_save_file):
                # Make file writable before deleting
                try:
                    os.chmod(self.keypad_save_file, 0o666)
                except:
                    pass
                os.remove(self.keypad_save_file)
            self.found_codes = []
            self.keypad_code = ""
            self.last_successful_code = ""
            self.status = "Keypad solver reset - all data cleared"
        except Exception as e:
            self.status = f"Could not reset keypad data: {e}"
    
    def fix_folder_permissions(self):
        """Fix folder permissions to allow file creation"""
        try:
            # Try to make folder writable
            os.chmod(self.app_folder, 0o777)
            print(f"✓ Folder permissions fixed: {self.app_folder}")
        except PermissionError:
            print(f"WARNING: Cannot fix folder permissions (permission denied)")
            print(f"Folder: {self.app_folder}")
            print(f"Try running as Administrator")
        except Exception as e:
            print(f"WARNING: Error fixing folder permissions: {e}")
    
    def reset_all_data(self):
        """Reset ALL saved application data"""
        try:
            # Delete settings.txt
            if os.path.exists('settings.txt'):
                try:
                    os.chmod('settings.txt', 0o666)
                except:
                    pass
                os.remove('settings.txt')
            
            # Delete keypad_resume.txt
            if os.path.exists(self.keypad_save_file):
                try:
                    os.chmod(self.keypad_save_file, 0o666)
                except:
                    pass
                os.remove(self.keypad_save_file)
            
            # Delete keys.txt
            if os.path.exists(self.keys_save_file):
                try:
                    os.chmod(self.keys_save_file, 0o666)
                except:
                    pass
                os.remove(self.keys_save_file)
            
            # Reset all variables
            self.found_codes = []
            self.keypad_code = ""
            self.last_successful_code = ""
            self.blocked_keys.clear()
            
            # Recreate default settings
            self.create_default_settings()
            self.load_settings()
            
            self.status = "✓ ALL DATA RESET - Fresh start!"
        except Exception as e:
            self.status = f"Error resetting data: {e}"

    def find_game_process(self):
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name']
                if any(game.lower() in proc_name.lower() for game in ['zombi', 'zombie']):
                    return proc_name
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def check_game_running(self):
        while self.running:
            try:
                if not self.pm:
                    found_process = self.find_game_process()
                    if found_process:
                        try:
                            self.pm = pymem.Pymem(found_process)
                            self.process_found = True
                            self.process_name = found_process
                            self.status = f"✓ GAME DETECTED ({found_process})"
                        except:
                            self.status = f"Found: {found_process} (Access Denied)"
                            self.pm = None
                    else:
                        self.pm = None
                        self.process_found = False
                        self.status = "Waiting for ZombiU..."
                else:
                    try:
                        self.pm.read_bytes(self.pm.base_address, 1)
                    except:
                        self.pm = None
                        self.process_found = False
                        self.status = "Game closed"
            except:
                self.pm = None
                self.process_found = False
            time.sleep(2)

    def mark_code_successful(self, code):
        self.last_successful_code = code
        self.status = f"✓ SUCCESS! Code {code} saved as last good code"
        self.add_found_code(code, "Successful")

    def try_manual_code(self, code):
        try:
            if not code or len(code) != 4 or not code.isdigit():
                self.status = "Invalid code (need 4 digits: 0-9)"
                return
            
            self.keypad_code = code
            self.status = f"🔑 Trying: {code}"
            
            for digit in code:
                try:
                    keyboard.press_and_release(digit)
                    time.sleep(0.08)
                except Exception as e:
                    print(f"[ERROR] Failed to press key {digit}: {e}")
                    self.status = f"Error pressing key {digit}"
                    return
            
            try:
                keyboard.press_and_release('enter')
                time.sleep(0.15)
            except Exception as e:
                print(f"[ERROR] Failed to press enter: {e}")
                self.status = "Error pressing enter key"
                return
        except Exception as e:
            print(f"[ERROR] try_manual_code: {e}")
            self.status = f"Error: {str(e)[:50]}"

    def add_found_code(self, code, location):
        try:
            if not code or not isinstance(code, str):
                return False
            
            # Only add valid 4-digit codes
            if len(code) != 4 or not code.isdigit():
                return False
            
            if not any(c[0] == code for c in self.found_codes):
                self.found_codes.append((code, location))
                self.save_keypad_resume()  # Auto-save when code is added
                return True
            return False
        except Exception as e:
            print(f"[ERROR] add_found_code: {e}")
            return False

    def start_countdown_then_clicker(self):
        """Show countdown in status, then start auto-clicker"""
        def countdown_thread():
            countdown_time = self.autostart_timer_delay if self.autostart_timer_enabled else 0
            
            # Show resuming message if there are saved codes
            if self.found_codes:
                self.status = f"Resuming now... {len(self.found_codes)} saved codes loaded"
                time.sleep(1)
            
            if countdown_time <= 0:
                self.status = "Starting auto-clicker NOW!"
                time.sleep(0.5)
                self.start_screen_clicker()
                return
            
            for i in range(countdown_time, 0, -1):
                if not self.circle_ready:
                    self.status = "Countdown cancelled"
                    return
                
                self.status = f"AUTO-START IN {i} SECONDS - Press F1 to cancel"
                
                # Beep on countdown
                if self.beep_countdown and self.sound_enabled:
                    try:
                        import winsound
                        if i <= 3:
                            winsound.Beep(1000 + (i * 200), 200)
                        else:
                            winsound.Beep(800, 150)
                    except:
                        print('\a')
                
                time.sleep(1)
            
            # Final beep
            if self.sound_enabled:
                try:
                    import winsound
                    winsound.Beep(1500, 400)
                except:
                    print('\a')
            
            self.status = "Starting auto-clicker NOW!"
            time.sleep(0.5)
            self.start_screen_clicker()
        
        self.autostart_timer_running = True
        self.autostart_timer_start_time = time.time()
        Thread(target=countdown_thread, daemon=True).start()

    def start_screen_clicker(self):
        # Safety check: ensure we have valid circle positions
        if not self.circle_positions or len(self.circle_positions) < 12:
            self.status = "⚠ Place 12 circles first! Current: " + str(len(self.circle_positions) if self.circle_positions else 0)
            self.auto_clicking = False
            return
        
        # Verify all positions are valid
        invalid_positions = []
        for i, pos in enumerate(self.circle_positions):
            if pos is None or len(pos) < 2 or pos[0] is None or pos[1] is None:
                invalid_positions.append(i)
        
        if invalid_positions:
            self.status = f"⚠ Invalid circle positions: {invalid_positions}. Place circles again!"
            self.auto_clicking = False
            return
        
        if self.auto_clicking:
            self.auto_clicking = False
            self.status = "Screen clicker stopped"
            return
        
        self.auto_clicking = True
        self.status = "🖱️ Starting..."
        Thread(target=self._screen_clicker_thread, daemon=True).start()

    def _screen_clicker_thread(self):
        # Initial wait - reduced for faster start
        time.sleep(0.5)
        
        # Reload resume data to ensure fresh data from file
        self.load_keypad_resume()
        
        # Check if resuming from previous session
        resuming = self.keypad_code  # Only check keypad_code for display
        if resuming:
            self.status = f"RESUMING from: {self.keypad_code} (Check keypad_resume.txt for all codes)"
        else:
            self.status = "Auto-clicking started!"
        
        button_map = {
            '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5,
            '7': 6, '8': 7, '9': 8, '0': 9, 'enter': 10, 'clear': 11
        }
        
        common_codes = ['0451', '1984', '1337', '4815', '1234', '0000', '1111', '4321']
        
        # Get already tried codes from found_codes
        tried_codes = set()
        for code_list in self.found_codes:
            tried_codes.add(code_list[0])
        
        # If resuming from a common code, skip to that code
        last_common_index = -1
        if resuming and self.keypad_code and self.keypad_code in common_codes:
            last_common_index = common_codes.index(self.keypad_code)
            # Start from the next common code
            last_common_index += 1
        else:
            # Not resuming from common code, do all common codes first
            last_common_index = 0
        
        # Priority 1: Common Codes - Start from where we left off
        for i in range(last_common_index, len(common_codes)):
            if not self.auto_clicking:
                return
            code = common_codes[i]
            # Skip if already tried
            if code not in tried_codes:
                self._click_code_on_screen(code, button_map)
        
        # Priority 2: All Combinations - Continue from last position
        start_num = 0
        if resuming and self.keypad_code and len(self.keypad_code) == 4 and self.keypad_code not in common_codes:
            try:
                # Start from NEXT code after last tried
                start_num = int(self.keypad_code) + 1
            except ValueError:
                start_num = 0
        
        for num in range(start_num, 10000):
            if not self.auto_clicking:
                self.status = "Auto-clicker stopped"
                return
            
            code = f"{num:04d}"
            # Skip common codes and already tried codes
            if code not in common_codes and code not in tried_codes:
                self._click_code_on_screen(code, button_map)
        
        self.auto_clicking = False
        self.status = "All combinations clicked"

    def _click_code_on_screen(self, code, button_map):
        # Safety check: ensure circles are placed
        if not self.circle_positions or len(self.circle_positions) < 12:
            self.status = "ERROR: Not enough circles placed! Need 12 circles."
            self.auto_clicking = False
            return
        
        self.keypad_code = code
        self.status = f"Clicking: {code}"
        
        # Add this code to tried codes list for notepad file
        self.add_found_code(code, "Tried")
        
        try:
            for digit in code:
                if not self.auto_clicking:
                    return
                
                # Safety check for button_map
                if digit not in button_map:
                    print(f"[ERROR] Invalid digit in code: {digit}")
                    return
                
                pos_index = button_map[digit]
                
                # Safety check for circle_positions array
                if pos_index >= len(self.circle_positions):
                    print(f"[ERROR] Circle position {pos_index} out of bounds. Only {len(self.circle_positions)} circles placed.")
                    self.status = f"ERROR: Circle {pos_index} not placed!"
                    self.auto_clicking = False
                    return
                
                x, y = self.circle_positions[pos_index]
                
                # Validate coordinates
                if x is None or y is None:
                    print(f"[ERROR] Invalid coordinates for button {digit}")
                    self.status = f"ERROR: Invalid coordinates for {digit}"
                    self.auto_clicking = False
                    return
                
                pyautogui.moveTo(x, y, duration=0)
                time.sleep(0.005)
                pyautogui.mouseDown(x, y)
                time.sleep(0.02)
                pyautogui.mouseUp(x, y)
                time.sleep(self.click_delay)
            
            if not self.auto_clicking:
                return
            
            # Check ENTER button
            if button_map['enter'] >= len(self.circle_positions):
                print(f"[ERROR] ENTER button position out of bounds")
                self.status = "ERROR: ENTER button not placed!"
                self.auto_clicking = False
                return
            
            enter_x, enter_y = self.circle_positions[button_map['enter']]
            
            # Validate ENTER coordinates
            if enter_x is None or enter_y is None:
                print(f"[ERROR] Invalid ENTER coordinates")
                self.status = "ERROR: Invalid ENTER coordinates"
                self.auto_clicking = False
                return
            
            pyautogui.moveTo(enter_x, enter_y, duration=0)
            time.sleep(0.005)
            pyautogui.mouseDown(enter_x, enter_y)
            time.sleep(0.02)
            pyautogui.mouseUp(enter_x, enter_y)
            time.sleep(self.enter_delay)
            
            # Save AFTER complete code attempt (all codes saved to file)
            self.save_keypad_resume()
        
        except Exception as e:
            print(f"[ERROR] _click_code_on_screen: {e}")
            self.status = f"Error: {str(e)[:50]}"
            self.auto_clicking = False

    def toggle_key_blocker(self, key=None):
        if key == 'all':
            if len(self.blocked_keys) == len(self.available_keys):
                self.blocked_keys.clear()
                self.key_blocker_active = False
                self.status = "All keys unblocked"
            else:
                self.blocked_keys = set(self.available_keys)
                self.key_blocker_active = True
                self.status = "All keys blocked"
        elif key:
            if key in self.blocked_keys:
                self.blocked_keys.remove(key)
            else:
                self.blocked_keys.add(key)
            self.key_blocker_active = len(self.blocked_keys) > 0
            self.status = f"Blocked: {', '.join(self.blocked_keys)}" if self.blocked_keys else "No keys blocked"
        
        self._update_key_hooks()
    
    def add_key_to_blocker(self, key):
        """Add key to blocker with fast typing debounce"""
        current_time = time.time()
        
        # If same key pressed within 100ms, ignore it
        if self.last_added_key == key and (current_time - self.key_add_time) < 0.1:
            return False
        
        if key not in self.blocked_keys:
            self.blocked_keys.add(key)
            self.last_added_key = key
            self.key_add_time = current_time
            self.status = f"KEY ADDED: {key.upper()}"
            self._update_key_hooks()
            return True
        return False

    def _update_key_hooks(self):
        try:
            keyboard.unhook_all()
        except:
            pass
        
        # Key blocker should work even without game detection
        if self.key_blocker_active and self.blocked_keys and self.custom_keys_enabled:
            for key in self.blocked_keys:
                try:
                    keyboard.block_key(key)
                except Exception as e:
                    pass

    def toggle_timer(self):
        if not self.timer_active:
            self.timer_active = True
            self.timer_paused = False
            self.timer_start = time.time()
            self.timer_elapsed = 0
            self.status = "Timer started"
        elif self.timer_paused:
            self.timer_paused = False
            self.timer_start = time.time() - self.timer_elapsed
            self.status = "▶️ Timer resumed"
        else:
            self.timer_paused = True
            self.timer_elapsed = time.time() - self.timer_start
            self.status = "⏸️ Timer paused"

    def reset_timer(self):
        self.timer_active = False
        self.timer_paused = False
        self.timer_start = 0
        self.timer_elapsed = 0
        self.status = "Timer reset"

    def get_timer_display(self):
        if not self.timer_active:
            return "00:00:00.000"
        
        elapsed = self.timer_elapsed if self.timer_paused else time.time() - self.timer_start
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        milliseconds = int((elapsed % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

    def stop(self):
        self.running = False
        self.keypad_solving = False
        self.auto_clicking = False
        try:
            keyboard.unhook_all()
        except:
            pass

# ==============================================================================
# OVERLAY CLASS
# ==============================================================================
class CirclePlacer:
    def __init__(self, parent_trainer):
        self.trainer = parent_trainer
        self.window = None
        self.canvas = None
        self.circles = []
        self.undo_stack = []
        self.redo_stack = []
        self.active = False
        self.placing_mode = True
        self.current_circle = 0
        self.countdown_active = False
        self.preview_circle = None
        self.preview_parts = []
        self.check_key_thread = None
        self.mouse_click_thread = None
        self.mode_text = None
        self.overlay_visible = True
        self.click_through_mode = True
        self.f1_pressed = False
        self.x_pressed = False
        self.x_last_press_time = 0
        self.see_through_mode = False
        self.hwnd = None
        self.mouse_x = 0
        self.mouse_y = 0
        self.last_click_time = 0
        self.stop_threads = False  # FIX: Signal threads to stop cleanly

    def check_mouse_clicks(self):
        """FIX: Check mouse clicks without blocking and with proper thread control"""
        def on_click(x, y, button, pressed):
            if not self.active or not self.see_through_mode or not self.placing_mode or self.stop_threads:
                return
            if pressed and button == mouse.Button.left:
                try:
                    if keyboard.is_pressed('x'):
                        current_time = time.time()
                        if current_time - self.last_click_time > 0.3:
                            self.last_click_time = current_time
                            if self.current_circle < 12:
                                try:
                                    # FIX: Use 5ms delay instead of 0 to prevent GUI queue overflow
                                    if self.window and not self.stop_threads:
                                        self.window.after(5, lambda: self.place_circle_at_position(x, y))
                                except:
                                    pass
                    else:
                        self.trainer.status = "⚠️ HOLD X while clicking to place circles!"
                except:
                    pass
        try:
            with mouse.Listener(on_click=on_click) as listener:
                # FIX: Check stop_threads flag instead of just self.active
                while self.active and not self.stop_threads:
                    time.sleep(0.1)
        except:
            pass

    def check_keys_continuously(self):
        """FIX: Check keyboard input with proper thread control and reduced GUI queue buildup"""
        while self.active and not self.stop_threads:
            try:
                # Use timeout to prevent blocking
                try:
                    f1_pressed = keyboard.is_pressed('f1')
                except:
                    f1_pressed = False
                
                if f1_pressed:
                    if not self.f1_pressed:
                        self.f1_pressed = True
                        if self.countdown_active:
                            self.countdown_active = False
                            self.active = False
                            self.trainer.status = "Countdown CANCELLED by F1"
                            self.stop_threads = True
                            if self.window:
                                try:
                                    self.hide()
                                except:
                                    pass
                            return
                        if self.placing_mode and self.window and self.active:
                            self.trainer.status = "Circle placer CLOSED by F1"
                            self.active = False
                            self.stop_threads = True
                            try:
                                self.hide()
                            except:
                                pass
                            return
                        if self.trainer.auto_clicking:
                            self.trainer.auto_clicking = False
                            self.trainer.status = "AUTO-CLICKER STOPPED by F1!"
                        if self.window and self.active:
                            self.active = False
                            self.stop_threads = True
                            try:
                                self.hide()
                            except:
                                pass
                else:
                    self.f1_pressed = False
                
                x_pressed = keyboard.is_pressed('x')
                current_time = time.time()
                
                # Use try-except to prevent keyboard check from blocking
                try:
                    if keyboard.is_pressed('ctrl') and keyboard.is_pressed('z'):
                        if self.placing_mode:
                            self.undo_last_circle()
                            time.sleep(0.2)
                except:
                    pass
                
                try:
                    if keyboard.is_pressed('ctrl') and keyboard.is_pressed('y'):
                        if self.placing_mode:
                            self.redo_last_circle()
                            time.sleep(0.2)
                except:
                    pass
                
                try:
                    if keyboard.is_pressed('ctrl') and keyboard.is_pressed('r'):
                        if self.placing_mode:
                            self.reset_circles()
                            time.sleep(0.3)
                except:
                    pass
                
                if x_pressed and not self.x_pressed:
                    self.x_pressed = True
                    if current_time - self.x_last_press_time < 0.3:
                        self.see_through_mode = not self.see_through_mode
                        # FIX: Use 10ms delay instead of 0 to prevent GUI queue overflow
                        if self.window and not self.stop_threads:
                            try:
                                self.window.after(10, self._update_see_through_mode)
                            except:
                                pass
                    self.x_last_press_time = current_time
                elif not x_pressed:
                    self.x_pressed = False
                
                # Update preview circle - use non-blocking approach
                if self.see_through_mode and self.window and self.placing_mode and self.current_circle < 12 and not self.stop_threads:
                    try:
                        mouse_x, mouse_y = pyautogui.position()
                        # FIX: Use 10ms delay instead of 0 to prevent GUI queue overflow
                        if self.window and not self.stop_threads:
                            self.window.after(10, lambda mx=mouse_x, my=mouse_y: self.update_preview_circle(mx, my))
                    except:
                        pass
                elif not self.see_through_mode and not self.stop_threads:
                    try:
                        if self.window:
                            self.window.after(10, self.hide_preview_circle)
                    except:
                        pass
            except Exception as e:
                pass
            time.sleep(0.05)

    def _update_see_through_mode(self):
        """FIX: Update see-through mode with better error handling and thread control"""
        try:
            if not self.window or self.stop_threads:
                return
            
            if self.see_through_mode:
                try:
                    self.window.attributes('-alpha', self.trainer.overlay_opacity)
                except:
                    pass
                if self.hwnd:
                    try:
                        styles = ctypes.windll.user32.GetWindowLongW(self.hwnd, -20)
                        styles = styles | 0x80000 | 0x20
                        ctypes.windll.user32.SetWindowLongW(self.hwnd, -20, styles)
                    except:
                        pass
                if self.mode_text and self.canvas:
                    try:
                        self.canvas.itemconfig(self.mode_text, 
                            text="SEE-THROUGH ON! HOLD X + CLICK on game keypad!", 
                            fill='#00ff00')
                    except:
                        pass
                self.trainer.status = "See-through ON - HOLD X + click to place!"
            else:
                try:
                    self.window.attributes('-alpha', 0.65)
                except:
                    pass
                if self.hwnd:
                    try:
                        styles = ctypes.windll.user32.GetWindowLongW(self.hwnd, -20)
                        styles = styles & ~0x20
                        ctypes.windll.user32.SetWindowLongW(self.hwnd, -20, styles)
                    except:
                        pass
                if self.mode_text and self.canvas:
                    try:
                        self.canvas.itemconfig(self.mode_text, 
                            text="⚠️ Double-click X to see through & click game!", 
                            fill='#ff8800')
                    except:
                        pass
                self.trainer.status = "See-through mode OFF - Click on overlay to place"
        except:
            pass
    
    def update_preview_circle(self, x, y):
        if not self.canvas or self.current_circle >= 12:
            return
        self.hide_preview_circle()
        label_map = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '✓', '✖']
        glow = self.canvas.create_oval(
            x-40, y-40, x+40, y+40,
            outline='#ff00ff', width=12, fill='', dash=(5, 5)
        )
        self.preview_parts.append(glow)
        middle = self.canvas.create_oval(
            x-28, y-28, x+28, y+28,
            outline='#00ffff', width=10, fill='#ffff00', stipple='gray50'
        )
        self.preview_parts.append(middle)
        text = self.canvas.create_text(
            x, y, text=label_map[self.current_circle],
            fill='#ff0000', font=('Arial', 28, 'bold')
        )
        self.preview_parts.append(text)
    
    def hide_preview_circle(self):
        if self.canvas:
            for part in self.preview_parts:
                try:
                    self.canvas.delete(part)
                except:
                    pass
            self.preview_parts = []

    def place_circle_at_position(self, x, y):
        if self.current_circle >= 12 or not self.placing_mode:
            return
        circle_parts = []
        glow = self.canvas.create_oval(
            x-40, y-40, x+40, y+40,
            outline='#ff0000', width=10, fill=''
        )
        circle_parts.append(glow)
        middle = self.canvas.create_oval(
            x-28, y-28, x+28, y+28,
            outline='#ffff00', width=8, fill='#00ff00'
        )
        circle_parts.append(middle)
        circle = self.canvas.create_oval(
            x-22, y-22, x+22, y+22,
            outline='#ffffff', width=6, fill='#00ff00'
        )
        circle_parts.append(circle)
        label_map = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '✓', '✖']
        text = self.canvas.create_text(
            x, y, text=label_map[self.current_circle],
            fill='#000000', font=('Arial', 24, 'bold')
        )
        circle_parts.append(text)
        self.undo_stack.append((circle_parts, (x, y)))
        self.redo_stack.clear()
        self.circles.append(circle_parts)
        self.trainer.circle_positions.append((x, y))
        self.current_circle += 1
        self.trainer.status = f"Circle {self.current_circle} placed!"
        self.canvas.itemconfig(self.lbl_count, text=f"{self.current_circle}/12", fill='#00ff00')
        if self.current_circle < 12:
            instructions = f"Double-click X = See through | Hold X + Click = Place | F1 = Close"
            self.canvas.itemconfig(self.instruction_text, text=instructions, fill='#00ff00')
        else:
            self.canvas.itemconfig(self.instruction_text, 
                                  text="ALL 12 CIRCLES PLACED!\nClosing...",
                                  fill='#ffff00')
            self.placing_mode = False
            self.window.after(500, lambda: self.close_and_start_countdown())

    def show(self):
        if self.active:
            self.hide()
            return
        self.active = True
        self.stop_threads = False  # FIX: Reset thread control flag
        self.circles = []
        self.trainer.circle_positions = []
        self.current_circle = 0
        self.placing_mode = True
        self.overlay_visible = True
        self.click_through_mode = True
        self.f1_pressed = False
        self.x_pressed = False
        self.see_through_mode = False  # FIX: Always start in normal mode (not see-through)
        self.x_last_press_time = 0  # FIX: Reset X press timer
        
        self.window = tk.Toplevel()
        self.window.title("Circle Placer - Zombi Tools")
        self.window.attributes('-topmost', True)  # Always on top of game window
        self.window.attributes('-alpha', 0.65)  # Slight transparency
        self.window.attributes('-fullscreen', True)  # Cover entire screen
        self.window.configure(bg='#050505')
        self.window.focus_set()
        self.window.attributes('-disabled', False)
        self.window.update_idletasks()
        
        # Make window visible above fullscreen games on Windows
        try:
            import ctypes
            WS_EX_TOPMOST = 8
            WS_EX_NOACTIVATE = 0x08000000
            hwnd = ctypes.windll.user32.FindWindowW(None, "Circle Placer - Zombi Tools")
            if hwnd:
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001)
        except:
            pass
        
        self.hwnd = None
        try:
            self.hwnd = ctypes.windll.user32.FindWindowW(None, "Circle Placer - Zombi Tools")
        except:
            pass
            
        self.canvas = tk.Canvas(self.window, bg='#050505', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        instructions = f"Double-click X = See through | Hold X + Click = Place | F1 = Close"
        self.instruction_text = self.canvas.create_text(
            self.window.winfo_screenwidth() // 2, 50,
            text=instructions, fill='#00ff00', font=('Arial', 14, 'bold')
        )
        self.canvas.create_text(
            self.window.winfo_screenwidth() // 2, 110,
            text="Order: 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, ENTER, X", 
            fill='#ffff00', font=('Arial', 12, 'bold')
        )
        self.mode_text = self.canvas.create_text(
            self.window.winfo_screenwidth() // 2, 140,
            text="Double-click X to see through overlay", 
            fill='#ff8800', font=('Arial', 12)
        )
        
        # Display counter on top-right (smaller size)
        self.lbl_count = self.canvas.create_text(
            self.window.winfo_screenwidth() - 60, 30,
            text="0/12", fill='#ffff00', font=('Arial', 20, 'bold')
        )
        
        # Display visibility hint
        self.canvas.create_text(
            self.window.winfo_screenwidth() // 2, self.window.winfo_screenheight() - 50,
            text="⚠️ If crosshair is too small: Check 'Dev Tools' → Fullscreen Overlay settings", 
            fill='#ffaa00', font=('Arial', 10)
        )
        
        self.canvas.bind('<Button-1>', self.place_circle)
        
        # FIX: Only create threads if not already running
        if not self.check_key_thread or not self.check_key_thread.is_alive():
            self.check_key_thread = Thread(target=self.check_keys_continuously, daemon=True)
            self.check_key_thread.start()
        
        if not self.mouse_click_thread or not self.mouse_click_thread.is_alive():
            self.mouse_click_thread = Thread(target=self.check_mouse_clicks, daemon=True)
            self.mouse_click_thread.start()

    def place_circle(self, event):
        if not self.placing_mode or self.current_circle >= 12:
            return
        if self.see_through_mode:
            return
        self.hide_preview_circle()
        x, y = pyautogui.position()
        self.place_circle_at_position(x, y)
    
    def undo_last_circle(self):
        """Undo - remove last placed circle"""
        if not self.circles or self.current_circle == 0:
            return
        
        # Save position to redo stack
        last_pos = self.trainer.circle_positions[-1]
        self.redo_stack.append(last_pos)
        
        # Delete circle from canvas
        last_circle = self.circles[-1]
        for part in last_circle:
            try:
                self.canvas.delete(part)
            except:
                pass
        
        # Remove from tracking
        self.circles.pop()
        self.trainer.circle_positions.pop()
        self.current_circle -= 1
        self.placing_mode = True
        
        # Update UI
        self.canvas.itemconfig(self.lbl_count, text=f"{self.current_circle}/12", fill='#ffff00')
        instructions = f"Double-click X = See through | Hold X + Click = Place | F1 = Close"
        self.canvas.itemconfig(self.instruction_text, text=instructions, fill='#00ff00')
    
    def redo_last_circle(self):
        """Redo - place circle at saved position"""
        if not self.redo_stack:
            return
        
        # Get saved position
        position = self.redo_stack.pop()
        x, y = position
        
        if self.current_circle >= 12:
            return
        
        # Recreate circle at saved position
        circle_parts = []
        glow = self.canvas.create_oval(
            x-40, y-40, x+40, y+40,
            outline='#ff0000', width=10, fill=''
        )
        circle_parts.append(glow)
        
        middle = self.canvas.create_oval(
            x-28, y-28, x+28, y+28,
            outline='#ffff00', width=8, fill='#00ff00'
        )
        circle_parts.append(middle)
        
        circle = self.canvas.create_oval(
            x-22, y-22, x+22, y+22,
            outline='#ffffff', width=6, fill='#00ff00'
        )
        circle_parts.append(circle)
        
        label_map = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '✓', '✖']
        text = self.canvas.create_text(
            x, y, text=label_map[self.current_circle],
            fill='#000000', font=('Arial', 24, 'bold')
        )
        circle_parts.append(text)
        
        # Add back to tracking
        self.circles.append(circle_parts)
        self.trainer.circle_positions.append(position)
        self.current_circle += 1
        
        # Update UI
        self.canvas.itemconfig(self.lbl_count, text=f"{self.current_circle}/12", fill='#00ff00')
        if self.current_circle < 12:
            instructions = f"Double-click X = See through | Hold X + Click = Place | F1 = Close"
            self.canvas.itemconfig(self.instruction_text, text=instructions, fill='#00ff00')
        else:
            self.canvas.itemconfig(self.instruction_text, 
                                  text="ALL 12 CIRCLES PLACED!\nClosing...",
                                  fill='#ffff00')
            self.placing_mode = False
            self.window.after(500, lambda: self.close_and_start_countdown())

    def reset_circles(self):
        for circle_parts in self.circles:
            for part in circle_parts:
                self.canvas.delete(part)
        self.circles = []
        self.trainer.circle_positions = []
        self.current_circle = 0
        self.placing_mode = True
        self.trainer.circle_ready = False
        self.canvas.itemconfig(self.lbl_count, text="0/12", fill='#ffff00')
        instructions = f"Double-click X = See through!\nHOLD X + CLICK on game keypad!\nF1 = Close"
        self.canvas.itemconfig(self.instruction_text, text=instructions, fill='#ff8800')

    def close_and_start_countdown(self):
        if self.current_circle == 12:
            self.trainer.circle_ready = True
            self.hide()
            self.trainer.start_countdown_then_clicker()

    def hide(self):
        """FIX: Properly close window and stop threads + reset see-through mode"""
        self.active = False
        self.placing_mode = False
        self.countdown_active = False
        self.see_through_mode = False  # FIX: Reset see-through mode on close
        self.stop_threads = True  # FIX: Signal threads to stop
        
        # FIX: Give threads time to finish
        time.sleep(0.1)
        
        self.hide_preview_circle()
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None
            self.canvas = None
        self.trainer.status = "Overlay closed"

# ==============================================================================
# CROSSHAIR WINDOW
# ==============================================================================
class CrosshairWindow:
    def __init__(self, engine):
        self.engine = engine
        self.window = None
        self.canvas = None
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
    
    def show(self):
        if self.window:
            return
        
        self.window = tk.Toplevel()
        self.window.attributes('-transparentcolor', 'black')
        self.window.attributes('-alpha', 1.0)
        self.window.attributes('-topmost', True)
        self.window.overrideredirect(True)  # No window decorations
        
        # Get screen dimensions including taskbar
        import ctypes
        try:
            # Get actual screen size with taskbar
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            screen_height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        except:
            # Fallback to tkinter method
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
        
        if self.engine.crosshair_x is None:
            self.engine.crosshair_x = screen_width // 2
            self.engine.crosshair_y = screen_height // 2
        
        # Position at 0,0 with full screen size to cover taskbar
        self.window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.window.configure(bg='black')
        
        self.canvas = tk.Canvas(self.window, bg='black', highlightthickness=0, cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind('<Motion>', self.on_motion)
        self.canvas.bind('<Button-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        
        self.draw_crosshair()
    
    def hide(self):
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None
            self.canvas = None
    
    def draw_crosshair(self):
        if not self.canvas:
            return
        
        try:
            self.canvas.delete('all')
            x = int(self.engine.crosshair_x)
            y = int(self.engine.crosshair_y)
            size = int(self.engine.crosshair_size)
            color = self.engine.crosshair_color
            shape = self.engine.crosshair_shape
            width = int(self.engine.crosshair_width)
            
            # Draw based on shape
            if shape == 'circle':
                self.canvas.create_oval(x-size, y-size, x+size, y+size, outline=color, width=width)
            elif shape == 'triangle':
                points = [x, y-size, x+size, y+size, x-size, y+size]
                self.canvas.create_polygon(points, outline=color, fill='', width=width)
            elif shape == 'diamond':
                points = [x, y-size, x+size, y, x, y+size, x-size, y]
                self.canvas.create_polygon(points, outline=color, fill='', width=width)
            elif shape == 'square':
                self.canvas.create_rectangle(x-size, y-size, x+size, y+size, outline=color, width=width)
            elif shape == 'star':
                # 5-pointed star
                import math
                points = []
                for i in range(10):
                    angle = i * math.pi / 5 - math.pi / 2
                    r = size if i % 2 == 0 else size // 2
                    px = x + r * math.cos(angle)
                    py = y + r * math.sin(angle)
                    points.extend([px, py])
                self.canvas.create_polygon(points, outline=color, fill='', width=width)
            elif shape == 'cross':
                self.canvas.create_line(x, y-size, x, y+size, fill=color, width=width)
                self.canvas.create_line(x-size, y, x+size, y, fill=color, width=width)
            elif shape == 'plus':
                for offset in [-2, 0, 2]:
                    self.canvas.create_line(x+offset, y-size, x+offset, y+size, fill=color, width=width)
                    self.canvas.create_line(x-size, y+offset, x+size, y+offset, fill=color, width=width)
            elif shape == 'hexagon':
                import math
                points = []
                for i in range(6):
                    angle = i * math.pi / 3
                    px = x + size * math.cos(angle)
                    py = y + size * math.sin(angle)
                    points.extend([px, py])
                self.canvas.create_polygon(points, outline=color, fill='', width=width)
            elif shape == 'octagon':
                import math
                points = []
                for i in range(8):
                    angle = i * math.pi / 4
                    px = x + size * math.cos(angle)
                    py = y + size * math.sin(angle)
                    points.extend([px, py])
                self.canvas.create_polygon(points, outline=color, fill='', width=width)
            elif shape == 'pentagon':
                import math
                points = []
                for i in range(5):
                    angle = i * 2 * math.pi / 5 - math.pi / 2
                    px = x + size * math.cos(angle)
                    py = y + size * math.sin(angle)
                    points.extend([px, py])
                self.canvas.create_polygon(points, outline=color, fill='', width=width)
            elif shape == 'x-cross':
                import math
                self.canvas.create_line(x-size, y-size, x+size, y+size, fill=color, width=width)
                self.canvas.create_line(x+size, y-size, x-size, y+size, fill=color, width=width)
            else:
                # Default to circle if shape unknown
                self.canvas.create_oval(x-size, y-size, x+size, y+size, outline=color, width=width)
            
            # Center dot
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill=color)
            
            # Schedule next update
            if self.window:
                self.window.after(50, self.draw_crosshair)
        except Exception as e:
            print(f"Crosshair draw error: {e}")
    
    def on_motion(self, event):
        # Motion is handled by continuous draw_crosshair loop
        pass
    
    def on_press(self, event):
        if not self.engine.crosshair_locked:
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
    
    def on_drag(self, event):
        if self.dragging and not self.engine.crosshair_locked:
            delta_x = event.x - self.drag_start_x
            delta_y = event.y - self.drag_start_y
            self.engine.crosshair_x += delta_x
            self.engine.crosshair_y += delta_y
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.draw_crosshair()
    
    def on_release(self, event):
        self.dragging = False

# ==============================================================================
# GUI
# ==============================================================================
class TrainerGUI:
    def __init__(self, engine):
        self.engine = engine
        self.app_folder = engine.app_folder  # Get app folder from engine
        self.circle_placer = CirclePlacer(engine)
        self.crosshair_window = CrosshairWindow(engine)
        self.last_dev_mode = None  # Track dev mode changes
        self.is_fullscreen = False  # Track fullscreen state
        self.original_taskbar_state = None  # Store original Windows taskbar state
        
        # Show where files are being saved
        save_location = self.engine.app_folder
        self.engine.status = f"✓ Settings saved to: {save_location}"
        print(f"\n{'='*80}")
        print(f"SAVE LOCATION: {save_location}")
        print(f"{'='*80}\n")
        
        # Load settings FIRST so we know if dev mode is on
        self.engine.load_settings()
        
        # Save the original Windows taskbar state before any modifications
        self.save_original_taskbar_state()
        
        self.root = tk.Tk()
        self.root.title("Zombi Tools")
        self.root.geometry("450x900+50+50")  # Larger window
        
        self.root.attributes('-alpha', 0.92)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # Apply developer fullscreen overlay settings
        try:
            self.root.attributes('-topmost', self.engine.dev_always_on_top)
            self.root.attributes('-alpha', self.engine.dev_window_transparency)
        except:
            pass
        
        # Add exit handler to save data on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Load logo.png as window icon if it exists
        try:
            if os.path.exists('logo.png'):
                logo_image = Image.open('logo.png')
                logo_photo = ImageTk.PhotoImage(logo_image)
                self.root.iconphoto(False, logo_photo)
                self.logo_photo = logo_photo  # Keep a reference
        except Exception as e:
            pass  # Icon not available, continue without it
        
        self.main_frame = tk.Frame(self.root, bg='#0d0d0d', bd=3, relief='solid', 
                                   highlightthickness=2, highlightbackground='#00ff00')
        self.main_frame.pack(fill='both', expand=True)
        
        self.title_bar = tk.Frame(self.main_frame, bg='#1a1a1a', height=40)
        self.title_bar.pack(fill='x')
        self.title_bar.bind('<Button-1>', self.start_drag)
        self.title_bar.bind('<B1-Motion>', self.on_drag)
        
        # Logo and title
        logo_title_frame = tk.Frame(self.title_bar, bg='#1a1a1a')
        logo_title_frame.pack(side='left', padx=5, pady=5)
        
        # Try to load logo.png for title bar
        logo_path = os.path.join(self.app_folder, 'logo.png')
        try:
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                # Resize logo to fit title bar (30x30)
                logo_img = logo_img.resize((30, 30), Image.Resampling.LANCZOS)
                self.title_bar_logo = ImageTk.PhotoImage(logo_img)
                tk.Label(logo_title_frame, image=self.title_bar_logo, bg='#1a1a1a').pack(side='left', padx=3)
            else:
                # Show [LOGO] placeholder if not found (not emoji)
                tk.Label(logo_title_frame, text="[LOGO]", fg='#00ff00', bg='#1a1a1a',
                        font=('Arial', 9, 'bold')).pack(side='left', padx=3)
        except Exception as e:
            # Show [LOGO] placeholder if error loading image
            tk.Label(logo_title_frame, text="[LOGO]", fg='#00ff00', bg='#1a1a1a',
                    font=('Arial', 9, 'bold')).pack(side='left', padx=3)
        
        tk.Label(logo_title_frame, text="ZOMBI TOOLS", fg='#00ff00', bg='#1a1a1a',
                font=('Arial', 12, 'bold')).pack(side='left', padx=5)
        tk.Label(self.title_bar, text="v1.0", fg='#666', bg='#1a1a1a',
                font=('Arial', 8)).pack(side='left', padx=5)
        
        # Small crosshair popup button
        tk.Button(self.title_bar, text='⊕', fg='#00ff00', bg='#1a1a1a', bd=0,
                 command=self.open_crosshair_popup, font=('Arial', 14, 'bold'),
                 activebackground='#00ff22').pack(side='right', padx=2)
        
        tk.Button(self.title_bar, text='✖', fg='#ff3333', bg='#1a1a1a', bd=0,
                 command=self.close_app, font=('Arial', 12, 'bold'),
                 activebackground='#ff0000').pack(side='right', padx=8)
        
        tk.Button(self.title_bar, text='─', fg='#ffff00', bg='#1a1a1a', bd=0,
                 command=self.minimize, font=('Arial', 12, 'bold')).pack(side='right', padx=2)
        
        self.lbl_status = tk.Label(self.main_frame, text="Initializing...", fg='#ffff00',
                                   bg='#0d0d0d', font=('Arial', 9, 'bold'))
        self.lbl_status.pack(pady=8)
        
        tk.Frame(self.main_frame, height=2, bg='#00ff00').pack(fill='x', pady=5)
        
        # Create tab buttons ONLY if dev mode is enabled
        self.tab_frame = tk.Frame(self.main_frame, bg='#0d0d0d')
        self.tab_frame.pack(fill='x', padx=10, pady=5)
        
        self.btn_tab_main = tk.Button(self.tab_frame, text="MAIN", bg='#00ff00', fg='#000', 
                                      font=('Arial', 9, 'bold'), cursor='hand2',
                                      command=self.show_main_tab)
        self.btn_tab_main.pack(side='left', padx=2, ipadx=10)
        
        # Crosshair tab button
        self.btn_tab_crosshair = tk.Button(self.tab_frame, text="⊕ CROSSHAIR", bg='#333', fg='#00ff00',
                                          font=('Arial', 9, 'bold'), cursor='hand2',
                                          command=self.show_crosshair_tab)
        self.btn_tab_crosshair.pack(side='left', padx=2, ipadx=10)
        
        # Only show dev tab button if dev_mode is enabled in settings
        if self.engine.dev_mode:
            self.btn_tab_dev = tk.Button(self.tab_frame, text="⚙️ DEV TOOLS", bg='#333', fg='#ffaa00',
                                         font=('Arial', 9, 'bold'), cursor='hand2',
                                         command=self.show_dev_tab)
            self.btn_tab_dev.pack(side='left', padx=2, ipadx=10)
        else:
            self.btn_tab_dev = None
        
        # Content frame for tabs
        self.content_frame = tk.Frame(self.main_frame, bg='#0d0d0d')
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Main tab content
        self.main_tab_frame = tk.Frame(self.content_frame, bg='#0d0d0d')
        
        # Crosshair tab content
        self.crosshair_tab_frame = tk.Frame(self.content_frame, bg='#0d0d0d')
        self.create_crosshair_tab()
        
        # Sections
        self.create_keypad_section()
        tk.Frame(self.main_tab_frame, height=1, bg='#333').pack(fill='x', pady=5)
        self.create_key_blocker_section()
        tk.Frame(self.main_tab_frame, height=1, bg='#333').pack(fill='x', pady=5)
        self.create_timer_section()
        
        # Dev tab content (only create if dev_mode is enabled)
        if self.engine.dev_mode:
            self.dev_tab_frame = tk.Frame(self.content_frame, bg='#0d0d0d')
            self.create_dev_tools_tab()
        else:
            self.dev_tab_frame = None
        
        tk.Label(self.main_frame, text="2x X=See-through | HOLD X+Click=Place | Ctrl+R=Reset | F1=Stop | F3=Timer",
                fg='#666', bg='#0d0d0d', font=('Arial', 7)).pack(side='bottom', pady=5)
        
        # Show MAIN tab by default (no need to click)
        self.show_main_tab()
        
        # Update keybind labels with current settings
        self.update_keybind_labels()
        
        # Apply saved taskbar state on startup
        self.apply_saved_taskbar_state()
        
        self.update()
        self.x = 0
        self.y = 0

    def create_keypad_section(self):
        frame = tk.Frame(self.main_tab_frame, bg='#0d0d0d')
        frame.pack(fill='x', padx=0, pady=5)
        self.lbl_f1_keybind = tk.Label(frame, text="F1: KEYPAD SOLVER", fg='#00ff00', bg='#0d0d0d',
                font=('Arial', 10, 'bold'))
        self.lbl_f1_keybind.pack(anchor='w')
        self.lbl_keypad = tk.Label(frame, text="Code: ----", fg='#00ffff', bg='#000000',
                                   font=('Courier', 12, 'bold'), relief='sunken', bd=2)
        self.lbl_keypad.pack(pady=5, fill='x')
        self.lbl_last_code = tk.Label(frame, text="Last Good Code: None", fg='#ffaa00', bg='#000000',
                                      font=('Courier', 10, 'bold'), relief='sunken', bd=2)
        self.lbl_last_code.pack(pady=3, fill='x')
        
        manual_frame = tk.Frame(frame, bg='#0d0d0d')
        manual_frame.pack(fill='x', pady=3)
        tk.Label(manual_frame, text="Manual:", fg='#888', bg='#0d0d0d',
                font=('Arial', 8)).pack(side='left', padx=2)
        self.entry_code = tk.Entry(manual_frame, width=6, font=('Courier', 12, 'bold'),
                                   bg='#1a1a1a', fg='#00ff00', justify='center',
                                   relief='sunken', bd=2)
        self.entry_code.pack(side='left', padx=2)
        tk.Button(manual_frame, text="Try", command=self.try_manual_code,
                 bg='#333', fg='white', font=('Arial', 8, 'bold'),
                 cursor='hand2').pack(side='left', padx=2, ipady=2, ipadx=8)
        tk.Button(manual_frame, text="Good", command=self.mark_code_good,
                 bg='#2a5', fg='white', font=('Arial', 8, 'bold'),
                 cursor='hand2').pack(side='left', padx=2, ipady=2, ipadx=8)
        
        # Reset button frame
        reset_frame = tk.Frame(frame, bg='#0d0d0d')
        reset_frame.pack(fill='x', pady=2)
        self.btn_reset_keypad = tk.Button(reset_frame, text="Reset Keypad", command=self.reset_keypad_solver,
                 bg='#a52', fg='white', bd=1, font=('Arial', 8, 'bold'),
                 cursor='hand2')
        self.btn_reset_keypad.pack(side='left', padx=2, ipady=2, ipadx=8)
        
        btn_frame2 = tk.Frame(frame, bg='#0d0d0d')
        btn_frame2.pack(fill='x', pady=3)
        self.btn_place_circles = tk.Button(btn_frame2, text="Place Circles & Auto-Start", command=self.circle_placer.show,
                 bg='#2a2', fg='white', font=('Arial', 9, 'bold'), bd=1,
                 cursor='hand2')
        self.btn_place_circles.pack(pady=3, ipady=6, ipadx=10, fill='x')
        tk.Label(frame, text="2x click X = See-through | HOLD X + click = Place!", fg='#ff8800',
                bg='#0d0d0d', font=('Arial', 8, 'bold')).pack(pady=2)
        tk.Label(frame, text="Auto-starts after 12 circles | 10sec delay | F1 to stop", fg='#888',
                bg='#0d0d0d', font=('Arial', 7, 'italic')).pack(pady=2)
        self.lbl_found = tk.Label(frame, text="Found Codes: None", fg='#ffaa00',
                                 bg='#0d0d0d', font=('Arial', 8), justify='left')
        self.lbl_found.pack(anchor='w', pady=3)
        self.lbl_resume_status = tk.Label(frame, text="Resume: ---", fg='#00ff00',
                                          bg='#0d0d0d', font=('Arial', 8), justify='left')
        self.lbl_resume_status.pack(anchor='w', pady=2)
    
    def try_manual_code(self):
        code = self.entry_code.get().strip()
        if not code:
            self.engine.status = "Enter a code first!"
            return
        if len(code) != 4 or not code.isdigit():
            self.engine.status = "Code must be 4 digits (0-9)!"
            return
        try:
            self.engine.try_manual_code(code)
        except Exception as e:
            self.engine.status = f"Error trying code: {str(e)[:50]}"
            print(f"[ERROR] try_manual_code: {e}")
    
    def mark_code_good(self):
        code = self.entry_code.get().strip()
        if not code:
            self.engine.status = "Enter a code first!"
            return
        if len(code) != 4 or not code.isdigit():
            self.engine.status = "Code must be 4 digits (0-9)!"
            return
        try:
            self.engine.mark_code_successful(code)
            self.engine.save_keypad_resume()  # Save after successful code
            self.entry_code.delete(0, tk.END)
            self.engine.status = f"✓ Code {code} saved!"
        except Exception as e:
            self.engine.status = f"Error saving code: {str(e)[:50]}"
            print(f"[ERROR] mark_code_good: {e}")
    
    def reset_keypad_solver(self):
        """Reset keypad solver with confirmation - disabled only during countdown"""
        from tkinter import messagebox
        
        # ONLY block if auto-clicker or COUNTDOWN is running
        # Don't block for paused timer or manual timer
        if self.engine.auto_clicking:
            messagebox.showerror("Cannot Reset", 
                                "⚠ Auto-clicker is running!\n\n"
                                "Stop the auto-clicker first (press F1)\n"
                                "Then you can reset keypad data.")
            self.engine.status = "⚠ Stop auto-clicker before resetting!"
            return
        
        # ONLY block if countdown (autostart_timer) is RUNNING, not paused
        if self.engine.autostart_timer_running:
            messagebox.showerror("Cannot Reset", 
                                "⚠ Countdown is running!\n\n"
                                "Wait for countdown to finish or press F1\n"
                                "Then you can reset keypad data.")
            self.engine.status = "⚠ Stop countdown before resetting!"
            return
        
        # Allow reset even if manual timer is active (doesn't affect keypad)
        # (removed timer_active check - only countdown matters)
        
        # All safe - proceed with reset
        result = messagebox.askyesno("Reset Keypad Solver", 
                                     "Delete all saved keypad codes?\n\n"
                                     "⚠ This cannot be undone!\n\n"
                                     "Are you sure?")
        if result:
            try:
                self.engine.reset_keypad_resume()
                self.update_found_codes()
                self.engine.status = "✓ All keypad data reset!"
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset: {str(e)[:100]}")
                self.engine.status = f"Error resetting: {str(e)[:50]}"
            
    def update_found_codes(self):
        if self.engine.found_codes:
            # Show ONLY the LAST found code in GUI
            last_code = self.engine.found_codes[-1][0]
            self.lbl_found.config(text=f"Found Codes: {last_code}")
            self.lbl_resume_status.config(text="Resume: Yes")
        else:
            # Show current code being tried if auto-clicker is running
            if self.engine.auto_clicking and self.engine.keypad_code:
                self.lbl_found.config(text=f"Found Codes: Trying {self.engine.keypad_code}")
            # If stopped (not clicking), keep the last code frozen
            elif not self.engine.auto_clicking and self.engine.keypad_code:
                self.lbl_found.config(text=f"Found Codes: Last {self.engine.keypad_code}")
            else:
                self.lbl_found.config(text="Found Codes: None")
            
            # Resume status - show bar if nothing, Yes if has data
            if self.engine.found_codes or self.engine.keypad_code:
                self.lbl_resume_status.config(text="Resume: Yes")
            else:
                self.lbl_resume_status.config(text="Resume: ---")

    def create_key_blocker_section(self):
        frame = tk.Frame(self.main_tab_frame, bg='#0d0d0d')
        frame.pack(fill='x', padx=0, pady=5)
        self.lbl_f2_keybind = tk.Label(frame, text="KEY BLOCKER", fg='#00ff00', bg='#0d0d0d',
                font=('Arial', 10, 'bold'))
        self.lbl_f2_keybind.pack(anchor='w')
        btn_frame1 = tk.Frame(frame, bg='#0d0d0d')
        btn_frame1.pack(fill='x', pady=2)
        for key in self.engine.available_keys[:3]:
            btn = tk.Button(btn_frame1, text=key.upper(),
                           command=lambda k=key: self.toggle_key_btn(k),
                           bg='#333', fg='#ff4444', bd=1, width=8,
                           font=('Arial', 8, 'bold'), cursor='hand2')
            btn.pack(side='left', padx=2, ipady=3)
            setattr(self, f'btn_{key}', btn)
        btn_frame2 = tk.Frame(frame, bg='#0d0d0d')
        btn_frame2.pack(fill='x', pady=2)
        for key in self.engine.available_keys[3:]:
            btn = tk.Button(btn_frame2, text=key.upper(),
                           command=lambda k=key: self.toggle_key_btn(k),
                           bg='#333', fg='#ff4444', bd=1, width=8,
                           font=('Arial', 8, 'bold'), cursor='hand2')
            btn.pack(side='left', padx=2, ipady=3)
            setattr(self, f'btn_{key}', btn)
        self.btn_all_keys = tk.Button(btn_frame2, text="ALL", command=lambda: self.toggle_all_keys(),
                 bg='#555', fg='white', bd=1, width=8, font=('Arial', 8, 'bold'),
                 cursor='hand2')
        self.btn_all_keys.pack(side='left', padx=2, ipady=3)
        
        btn_frame3 = tk.Frame(frame, bg='#0d0d0d')
        btn_frame3.pack(fill='x', pady=2)
        tk.Button(btn_frame3, text="Reset Keys", command=self.reset_key_blocker,
                 bg='#a52', fg='white', bd=1, width=8, font=('Arial', 8, 'bold'),
                 cursor='hand2').pack(side='left', padx=2, ipady=3)
        
        # Advanced Options button for all keyboard keys
        tk.Button(btn_frame3, text="Advanced Keys", command=self.open_advanced_keys_dialog,
                 bg='#3366ff', fg='white', bd=1, width=12, font=('Arial', 8, 'bold'),
                 cursor='hand2').pack(side='left', padx=2, ipady=3)
        
        # Enable/Disable custom key blocker section
        custom_enable_frame = tk.Frame(frame, bg='#0d0d0d')
        custom_enable_frame.pack(fill='x', pady=3, padx=2)
        tk.Label(custom_enable_frame, text="Custom Keys:", fg='#888', bg='#0d0d0d',
                font=('Arial', 8)).pack(side='left', padx=2)
        self.var_custom_blocker_enabled = tk.BooleanVar(value=True)
        tk.Checkbutton(custom_enable_frame, text="Enabled", variable=self.var_custom_blocker_enabled,
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.toggle_custom_blocker_section).pack(side='left', padx=2)
        
        # Custom key blocker entry
        self.custom_frame = tk.Frame(frame, bg='#0d0d0d')
        self.custom_frame.pack(fill='x', pady=3)
        tk.Label(self.custom_frame, text="Add Key:", fg='#888', bg='#0d0d0d',
                font=('Arial', 8)).pack(side='left', padx=2)
        
        # Create entry with character limit (1 character max)
        self.entry_custom_keys = tk.Entry(self.custom_frame, width=3, font=('Courier', 9),
                                          bg='#1a1a1a', fg='#00ff00', justify='center',
                                          relief='sunken', bd=1)
        self.entry_custom_keys.pack(side='left', padx=2)
        
        # Bind KeyRelease to auto-add key
        self.entry_custom_keys.bind('<KeyRelease>', self.limit_key_input)
        
        # Add button (optional, for manual add)
        tk.Button(self.custom_frame, text="Add", command=self.add_custom_key_blocker,
                 bg='#2a5', fg='white', bd=1, font=('Arial', 8, 'bold'),
                 cursor='hand2').pack(side='left', padx=2, ipady=2, ipadx=5)
        
        # Custom blocked keys list with scrollbar (COMPACT)
        self.list_frame = tk.Frame(frame, bg='#0d0d0d', height=80)  # Fixed height instead of expand
        self.list_frame.pack(fill='x', padx=2, pady=2)
        self.list_frame.pack_propagate(False)  # Don't expand beyond specified height
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(self.list_frame, bg='#333', activebackground='#555')
        scrollbar.pack(side='right', fill='y')
        
        # Create canvas for scrolling
        self.custom_keys_canvas = tk.Canvas(self.list_frame, bg='#0d0d0d', highlightthickness=0,
                                           height=80, yscrollcommand=scrollbar.set)
        self.custom_keys_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.custom_keys_canvas.yview)
        
        # Create frame inside canvas to hold checkboxes
        self.custom_keys_frame = tk.Frame(self.custom_keys_canvas, bg='#0d0d0d')
        self.custom_keys_window = self.custom_keys_canvas.create_window((0, 0), window=self.custom_keys_frame, anchor='nw')
        
        # Bind canvas resize to update scroll region
        def on_frame_configure(event=None):
            self.custom_keys_canvas.configure(scrollregion=self.custom_keys_canvas.bbox('all'))
        
        self.custom_keys_frame.bind('<Configure>', on_frame_configure)
        self.custom_keys_canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        
        # Dictionary to store checkbox variables for custom keys
        self.custom_key_vars = {}
        
        # Populate with saved keys
        self.populate_blocked_keys_listbox()
        
        # Control buttons for custom keys (removed - use X button on each key)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling in custom keys canvas"""
        try:
            if hasattr(self, 'custom_keys_canvas'):
                self.custom_keys_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except:
            pass
    
    def populate_blocked_keys_listbox(self):
        """Populate scrollable frame with custom keys as checkboxes"""
        # Clear existing checkboxes
        for widget in self.custom_keys_frame.winfo_children():
            widget.destroy()
        self.custom_key_vars.clear()
        
        # Create checkbox for each custom key (not preset keys)
        custom_keys = sorted([k for k in self.engine.blocked_keys if k not in self.engine.available_keys])
        
        if not custom_keys:
            tk.Label(self.custom_keys_frame, text="No custom keys", fg='#666', bg='#0d0d0d',
                    font=('Arial', 8)).pack(pady=5)
        else:
            for key in custom_keys:
                # Create frame for each key
                key_frame = tk.Frame(self.custom_keys_frame, bg='#0d0d0d')
                key_frame.pack(fill='x', padx=5, pady=2)
                
                # Checkbox variable
                var = tk.BooleanVar(value=True)  # All keys in blocked_keys are enabled
                self.custom_key_vars[key] = var
                
                # Checkbox
                checkbox = tk.Checkbutton(key_frame, text=key.upper(), variable=var,
                                         bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                                         font=('Arial', 8),
                                         command=lambda k=key: self.toggle_custom_key_checkbox(k))
                checkbox.pack(side='left', padx=2)
                
                # Delete button
                tk.Button(key_frame, text="X", bg='#a52', fg='white', width=2, font=('Arial', 7),
                         command=lambda k=key: self.remove_custom_key_by_key(k)).pack(side='left', padx=1)
    
    def toggle_custom_key_checkbox(self, key):
        """Toggle custom key enable/disable"""
        try:
            is_enabled = self.custom_key_vars[key].get()
            
            if is_enabled:
                # Enable - add to blocked keys
                if key not in self.engine.blocked_keys:
                    self.engine.blocked_keys.add(key)
            else:
                # Disable - remove from blocked keys
                if key in self.engine.blocked_keys:
                    self.engine.blocked_keys.discard(key)
            
            self.engine.key_blocker_active = len(self.engine.blocked_keys) > 0
            self.engine.save_blocked_keys()
            self.engine._update_key_hooks()
            self.engine.status = f"Key {key.upper()}: {'Enabled' if is_enabled else 'Disabled'} (saved)"
        except Exception as e:
            print(f"Error toggling key {key}: {e}")
    
    def remove_custom_key_by_key(self, key):
        """Remove custom key by key name"""
        try:
            if key in self.engine.blocked_keys:
                self.engine.blocked_keys.discard(key)
            
            self.engine.key_blocker_active = len(self.engine.blocked_keys) > 0
            self.engine.save_blocked_keys()
            self.engine._update_key_hooks()
            self.engine.status = f"Removed: {key.upper()} (saved)"
            self.populate_blocked_keys_listbox()
        except Exception as e:
            print(f"Error removing key {key}: {e}")
    
    def toggle_custom_blocker_section(self):
        """Enable/disable custom key blocker - when ENABLED, custom keys BLOCK. When DISABLED, they DON'T block."""
        self.engine.custom_keys_enabled = self.var_custom_blocker_enabled.get()
        
        if self.var_custom_blocker_enabled.get():
            # ENABLED = Show UI and ACTIVATE blocking
            self.custom_frame.pack(fill='x', pady=3)
            self.list_frame.pack(fill='both', padx=2, pady=2, expand=True)
            self.engine.status = "✓ Custom key blocking ENABLED"
        else:
            # DISABLED = Hide UI and DEACTIVATE blocking
            self.custom_frame.pack_forget()
            self.list_frame.pack_forget()
            self.engine.status = "✓ Custom key blocking DISABLED"
        
        self.engine._update_key_hooks()

    def toggle_key_btn(self, key):
        self.engine.toggle_key_blocker(key)
        btn = getattr(self, f'btn_{key}')
        if key in self.engine.blocked_keys:
            btn.config(fg='#00ff00', relief='sunken', bg='#1a5')
        else:
            btn.config(fg='#ff4444', relief='raised', bg='#333')
        
        # Save changes
        self.engine.save_blocked_keys()
        
        # Update listbox
        self.populate_blocked_keys_listbox()
    
    def toggle_all_keys(self):
        """Toggle ALL preset keys - keeps custom keys intact"""
        # Check if all preset keys are blocked
        preset_keys_blocked = all(key in self.engine.blocked_keys for key in self.engine.available_keys)
        
        # Get custom keys (not in preset list)
        custom_keys = set(k for k in self.engine.blocked_keys if k not in self.engine.available_keys)
        
        if preset_keys_blocked:
            # Unblock all preset keys, keep custom keys
            for key in self.engine.available_keys:
                self.engine.blocked_keys.discard(key)
            self.btn_all_keys.config(fg='white', bg='#555', relief='raised')
            for key in self.engine.available_keys:
                btn = getattr(self, f'btn_{key}')
                btn.config(fg='#ff4444', relief='raised', bg='#333')
        else:
            # Block all preset keys, keep custom keys
            for key in self.engine.available_keys:
                self.engine.blocked_keys.add(key)
            self.btn_all_keys.config(fg='#00ff00', bg='#1a5', relief='sunken')
            for key in self.engine.available_keys:
                btn = getattr(self, f'btn_{key}')
                btn.config(fg='#00ff00', relief='sunken', bg='#1a5')
        
        self.engine.key_blocker_active = len(self.engine.blocked_keys) > 0
        
        # Save changes
        self.engine.save_blocked_keys()
        self.engine._update_key_hooks()
        self.populate_blocked_keys_listbox()
    
    def reset_key_blocker(self):
        """Reset ONLY preset keys - keeps custom keys"""
        # Keep custom keys (not in preset list)
        custom_keys = set(k for k in self.engine.blocked_keys if k not in self.engine.available_keys)
        
        # Clear all keys then re-add only custom ones
        self.engine.blocked_keys.clear()
        self.engine.blocked_keys = custom_keys
        
        # Reset buttons to default state
        self.btn_all_keys.config(fg='white', bg='#555', relief='raised')
        for key in self.engine.available_keys:
            btn = getattr(self, f'btn_{key}')
            btn.config(fg='#ff4444', relief='raised', bg='#333')
        
        self.engine.key_blocker_active = len(self.engine.blocked_keys) > 0
        
        # Save changes
        self.engine.save_blocked_keys()
        self.engine._update_key_hooks()
        self.populate_blocked_keys_listbox()
        self.engine.status = "Preset keys reset"
    
    def open_advanced_keys_dialog(self):
        """Open dialog with all available keyboard keys to select from"""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("🔑 Advanced Key Selection")
            dialog.geometry("600x700")
            dialog.configure(bg='#0d0d0d')
            dialog.attributes('-topmost', True)
            
            # Title
            tk.Label(dialog, text="Click keys to add them to blocked list",
                    fg='#00ff00', bg='#0d0d0d', font=('Arial', 9, 'bold')).pack(pady=5)
            
            # All keyboard keys available - organized efficiently
            all_keys = [
                # Row 1: Numbers and symbols
                ('Numbers', ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']),
                # Row 2: Top letter row
                ('Top Row', ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']),
                # Row 3: Middle letter row
                ('Middle Row', ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l']),
                # Row 4: Bottom letter row
                ('Bottom Row', ['z', 'x', 'c', 'v', 'b', 'n', 'm']),
                # Row 5: Function Keys
                ('Function Keys', ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12']),
                # Row 6: Modifiers & Special
                ('Modifiers', ['shift', 'ctrl', 'alt']),
                ('Special', ['tab', 'capslock', 'space', 'enter', 'backspace', 'delete', 'escape']),
                ('Navigation', ['home', 'end', 'page_up', 'page_down', 'insert', 'up', 'down', 'left', 'right']),
            ]
            
            # Create scrollable frame
            canvas = tk.Canvas(dialog, bg='#0d0d0d', highlightthickness=0)
            scrollbar = tk.Scrollbar(dialog, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='#0d0d0d')
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Add key categories
            for category, keys in all_keys:
                cat_frame = tk.Frame(scrollable_frame, bg='#0d0d0d')
                cat_frame.pack(fill='x', padx=5, pady=2)
                
                tk.Label(cat_frame, text=category, fg='#ffaa00', bg='#0d0d0d',
                        font=('Arial', 7, 'bold')).pack(anchor='w', padx=3)
                
                # Grid layout - fit more keys per row
                keys_frame = tk.Frame(cat_frame, bg='#0d0d0d')
                keys_frame.pack(fill='x', padx=8, pady=1)
                
                for i, key in enumerate(keys):
                    is_blocked = key in self.engine.blocked_keys
                    btn_color = '#00ff00' if is_blocked else '#aaa'
                    btn_bg = '#1a3a1a' if is_blocked else '#333'
                    
                    tk.Button(keys_frame, text=key.upper(), width=4, height=1,
                             fg=btn_color, bg=btn_bg, font=('Arial', 6),
                             command=lambda k=key: self._toggle_advanced_key(k),
                             cursor='hand2').pack(side='left', padx=1, pady=0)
            
            canvas.pack(side='left', fill='both', expand=True, padx=5, pady=5)
            scrollbar.pack(side='right', fill='y')
            
            # Info label
            tk.Label(dialog, text="Green = Blocked | Gray = Not Blocked | Click to Toggle",
                    fg='#888', bg='#0d0d0d', font=('Arial', 7)).pack(pady=3)
            
            # Close button
            tk.Button(dialog, text="Close", command=dialog.destroy,
                     bg='#555', fg='white', font=('Arial', 8, 'bold')).pack(pady=3)
            
        except Exception as e:
            print(f"[ERROR] open_advanced_keys_dialog: {e}")
    
    def _toggle_advanced_key(self, key):
        """Toggle a key in the advanced dialog"""
        try:
            if key in self.engine.blocked_keys:
                self.engine.blocked_keys.discard(key)
                self.engine.status = f"Unblocked: {key.upper()}"
            else:
                self.engine.blocked_keys.add(key)
                self.engine.status = f"Blocked: {key.upper()}"
            
            self.engine.key_blocker_active = len(self.engine.blocked_keys) > 0
            self.engine.save_blocked_keys()
            self.engine._update_key_hooks()
            self.populate_blocked_keys_listbox()
            
            # Refresh UI without closing dialog - just update button colors
            # This will be updated on next dialog access
        except Exception as e:
            print(f"[ERROR] _toggle_advanced_key: {e}")
    
    def reset_all_data_btn(self):
        """Reset ALL data with confirmation - disabled during active operations"""
        from tkinter import messagebox
        
        # ONLY block if auto-clicker or COUNTDOWN is running
        # Don't block for paused timer or manual timer
        if self.engine.auto_clicking:
            messagebox.showerror("Cannot Reset", 
                                "⚠ Auto-clicker is running!\n\n"
                                "Stop the auto-clicker first (press F1)\n"
                                "Then you can reset all data.")
            self.engine.status = "⚠ Stop auto-clicker before resetting!"
            return
        
        # ONLY block if countdown (autostart_timer) is RUNNING
        if self.engine.autostart_timer_running:
            messagebox.showerror("Cannot Reset", 
                                "⚠ Countdown is running!\n\n"
                                "Wait for countdown to finish or press F1\n"
                                "Then you can reset all data.")
            self.engine.status = "⚠ Stop countdown before resetting!"
            return
        
        # Allow reset even if manual timer is active (doesn't affect operations)
        # (removed timer_active check - only countdown matters)
        
        # All safe - proceed with reset
        if messagebox.askyesno("Reset All Data", 
                              "⚠️  THIS WILL DELETE ALL SAVED DATA:\n\n"
                              "• settings.txt\n"
                              "• keypad_resume.txt\n"
                              "• keys.txt\n\n"
                              "Are you absolutely sure?"):
            try:
                self.engine.reset_all_data()
                self.populate_blocked_keys_listbox()
                messagebox.showinfo("Reset Complete", "✓ All data has been reset to defaults!")
                self.engine.status = "✓ All data reset!"
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset: {str(e)[:100]}")
                self.engine.status = f"Error resetting: {str(e)[:50]}"
    
    def limit_key_input(self, event):
        """Auto-add key when typed and prevent duplicates"""
        value = self.entry_custom_keys.get().strip().lower()
        
        # If more than 1 character, keep only first one
        if len(value) > 1:
            value = value[0]
            self.entry_custom_keys.delete(0, tk.END)
            self.entry_custom_keys.insert(0, value)
        
        # Auto-add if a key was entered and Enter was pressed
        if event.keysym == 'Return' and value:
            self.add_custom_key_blocker()
        elif value:
            # Auto-add after a short delay when key is released
            self.root.after(100, self.auto_add_key, value)
    
    def auto_add_key(self, key):
        """Auto-add key after debounce period"""
        current_value = self.entry_custom_keys.get().strip().lower()
        
        # Only add if the entry still contains the same key
        if current_value == key and key not in self.engine.blocked_keys:
            self.add_custom_key_blocker()
    
    def add_custom_key_blocker(self):
        """Add custom keys to block from text entry"""
        custom_keys_text = self.entry_custom_keys.get().strip().lower()
        if not custom_keys_text:
            return
        
        key = custom_keys_text[0]  # Take only first character
        
        # Allow ANY key to be blocked - no restrictions
        if key in self.engine.blocked_keys:
            self.engine.status = f"{key.upper()} already blocked"
            self.entry_custom_keys.delete(0, tk.END)
            return
        
        # Add to blocked keys using debounce method
        current_time = time.time()
        if self.engine.last_added_key == key and (current_time - self.engine.key_add_time) < 0.15:
            self.entry_custom_keys.delete(0, tk.END)
            return
        
        # Add to blocked keys
        self.engine.blocked_keys.add(key)
        self.engine.last_added_key = key
        self.engine.key_add_time = current_time
        
        self.engine.status = f"Blocked: {key.upper()} (saved to keys.txt)"
        self.engine.key_blocker_active = True
        
        # Keep textbox visible for more keys, just clear it
        self.entry_custom_keys.delete(0, tk.END)
        
        # Save blocked keys to file
        self.engine.save_blocked_keys()
        
        # Repopulate the list with the new key
        self.populate_blocked_keys_listbox()
        
        # Redraw the scroll region
        self.custom_keys_frame.update_idletasks()
        self.custom_keys_canvas.configure(scrollregion=self.custom_keys_canvas.bbox('all'))
        
        self.engine._update_key_hooks()
    
    def remove_selected_custom_key(self):
        """Remove selected custom key (kept for button compatibility)"""
        # This is called by button, but new system uses remove_custom_key_by_key
        pass

    def create_timer_section(self):
        frame = tk.Frame(self.main_tab_frame, bg='#0d0d0d')
        frame.pack(fill='x', padx=0, pady=5)
        self.lbl_f3_keybind = tk.Label(frame, text="F3: SPEEDRUN TIMER", fg='#00ff00', bg='#0d0d0d',
                font=('Arial', 10, 'bold'))
        self.lbl_f3_keybind.pack(anchor='w')
        self.lbl_timer = tk.Label(frame, text="00:00:00.000", fg='#00ffff', bg='#000000',
                                  font=('Courier', 20, 'bold'), relief='sunken', bd=3)
        self.lbl_timer.pack(pady=5, fill='x')
        btn_frame = tk.Frame(frame, bg='#0d0d0d')
        btn_frame.pack(fill='x', pady=3)
        tk.Button(btn_frame, text="▶/⏸ Start/Pause", command=self.engine.toggle_timer,
                 bg='#2a5', fg='white', bd=1, font=('Arial', 9, 'bold'),
                 cursor='hand2').pack(side='left', padx=2, ipady=4, ipadx=8)
        tk.Button(btn_frame, text="Reset", command=self.engine.reset_timer,
                 bg='#a52', fg='white', bd=1, font=('Arial', 9, 'bold'),
                 cursor='hand2').pack(side='left', padx=2, ipady=4, ipadx=8)
        
        # Reset ALL button at bottom of timer section
        btn_frame_bottom = tk.Frame(frame, bg='#0d0d0d')
        btn_frame_bottom.pack(fill='x', pady=3)
        tk.Button(btn_frame_bottom, text="Reset ALL Data", command=self.reset_all_data_btn,
                 bg='#cc3333', fg='white', bd=1, font=('Arial', 9, 'bold'),
                 cursor='hand2').pack(side='left', padx=2, ipady=4, ipadx=8)

    def create_crosshair_tab(self):
        """Create crosshair customization tab"""
        frame = tk.Frame(self.crosshair_tab_frame, bg='#0d0d0d')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        tk.Label(frame, text="⊕ CROSSHAIR CONTROL", fg='#00ffff', bg='#0d0d0d',
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Enable/Disable
        enable_frame = tk.Frame(frame, bg='#0d0d0d')
        enable_frame.pack(fill='x', pady=5)
        tk.Label(enable_frame, text="Enable:", fg='#888', bg='#0d0d0d').pack(side='left', padx=5)
        self.var_crosshair_enabled = tk.BooleanVar(value=self.engine.crosshair_enabled)
        tk.Checkbutton(enable_frame, text="ON", variable=self.var_crosshair_enabled,
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      command=self.update_crosshair_settings).pack(side='left', padx=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=5)
        
        # Shape dropdown
        shape_frame = tk.Frame(frame, bg='#0d0d0d')
        shape_frame.pack(fill='x', pady=5, padx=5)
        tk.Label(shape_frame, text="Shape:", fg='#00ff00', bg='#0d0d0d', font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        self.var_crosshair_shape = tk.StringVar(value=self.engine.crosshair_shape)
        shape_dropdown = tk.OptionMenu(shape_frame, self.var_crosshair_shape, 
                                       'circle', 'triangle', 'diamond', 'square', 'star', 'cross', 'plus',
                                       'hexagon', 'octagon', 'pentagon', 'x-cross',
                                       command=self.update_crosshair_settings)
        shape_dropdown.config(bg='#1a1a1a', fg='#00ff00', activebackground='#333')
        shape_dropdown.pack(side='left', padx=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=5)
        
        # Size with slider
        size_frame = tk.Frame(frame, bg='#0d0d0d')
        size_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(size_frame, text="Size:", fg='#00ff00', bg='#0d0d0d').pack(side='left', padx=5)
        self.var_crosshair_size = tk.IntVar(value=self.engine.crosshair_size)
        tk.Scale(size_frame, from_=5, to=100, variable=self.var_crosshair_size,
                bg='#0d0d0d', fg='#00ff00', orient=tk.HORIZONTAL,
                command=self.update_crosshair_settings).pack(side='left', padx=5, fill=tk.X, expand=True)
        
        # Line width (boldness) slider
        width_frame = tk.Frame(frame, bg='#0d0d0d')
        width_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(width_frame, text="Bold:", fg='#00ff00', bg='#0d0d0d').pack(side='left', padx=5)
        self.var_crosshair_width = tk.IntVar(value=2)  # Default width 2
        tk.Scale(width_frame, from_=1, to=8, variable=self.var_crosshair_width,
                bg='#0d0d0d', fg='#00ff00', orient=tk.HORIZONTAL,
                command=self.update_crosshair_settings).pack(side='left', padx=5, fill=tk.X, expand=True)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=5)
        
        # Color buttons
        tk.Label(frame, text="Color:", fg='#00ff00', bg='#0d0d0d',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=10, pady=3)
        
        color_frame1 = tk.Frame(frame, bg='#0d0d0d')
        color_frame1.pack(fill='x', padx=10, pady=3)
        for color, name in [('#00ff00', 'Green'), ('#ff0000', 'Red'), ('#0000ff', 'Blue')]:
            tk.Button(color_frame1, text=name, bg=color, fg='#000', width=10,
                     command=lambda c=color: self.set_crosshair_color(c)).pack(side='left', padx=2)
        
        color_frame2 = tk.Frame(frame, bg='#0d0d0d')
        color_frame2.pack(fill='x', padx=10, pady=3)
        for color, name in [('#ffff00', 'Yellow'), ('#ff00ff', 'Magenta'), ('#00ffff', 'Cyan')]:
            tk.Button(color_frame2, text=name, bg=color, fg='#000', width=10,
                     command=lambda c=color: self.set_crosshair_color(c)).pack(side='left', padx=2)
        
        # Custom color picker
        tk.Button(frame, text="Custom Color", bg='#444', fg='#fff', width=15,
                 command=self.pick_custom_color).pack(pady=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=5)
        
        # Lock position
        lock_frame = tk.Frame(frame, bg='#0d0d0d')
        lock_frame.pack(fill='x', pady=5, padx=10)
        tk.Label(lock_frame, text="Position:", fg='#888', bg='#0d0d0d').pack(side='left', padx=5)
        self.var_crosshair_locked = tk.BooleanVar(value=self.engine.crosshair_locked)
        tk.Checkbutton(lock_frame, text="Locked (Drag when unchecked)", variable=self.var_crosshair_locked,
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      command=self.update_crosshair_settings).pack(side='left', padx=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=5)
        
        # Taskbar visibility
        taskbar_frame = tk.Frame(frame, bg='#0d0d0d')
        taskbar_frame.pack(fill='x', pady=5, padx=10)
        tk.Label(taskbar_frame, text="Taskbar:", fg='#888', bg='#0d0d0d').pack(side='left', padx=5)
        self.var_taskbar_visible = tk.BooleanVar(value=False)  # Default OFF (hidden)
        tk.Checkbutton(taskbar_frame, text="Show Windows Bar", variable=self.var_taskbar_visible,
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      command=self.toggle_taskbar_visibility).pack(side='left', padx=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=5)
        
        # Reset button
        tk.Button(frame, text="Reset to Center", bg='#2a5', fg='white', width=20,
                 command=self.reset_crosshair_position).pack(pady=10)
    
    def update_crosshair_settings(self, *args):
        """Update crosshair settings (*args allows slider/menu to pass value)"""
        self.engine.crosshair_enabled = self.var_crosshair_enabled.get()
        self.engine.crosshair_size = self.var_crosshair_size.get()
        self.engine.crosshair_shape = self.var_crosshair_shape.get()
        self.engine.crosshair_locked = self.var_crosshair_locked.get()
        self.engine.crosshair_width = self.var_crosshair_width.get()
        
        # Show/Hide crosshair based on enabled state
        if self.engine.crosshair_enabled:
            # Crosshair ENABLED - show it
            if not self.crosshair_window.window:
                self.crosshair_window.show()
            self.crosshair_window.draw_crosshair()
        else:
            # Crosshair DISABLED - hide it completely
            self.crosshair_window.hide()
        
        # Sync popup if it exists
        self.sync_popup_with_tab()
        
        status_text = "Crosshair: ON ✓" if self.engine.crosshair_enabled else "Crosshair: OFF"
        self.engine.status = status_text
    
    def sync_crosshair_ui_from_engine(self):
        """Sync crosshair UI controls with engine values (for settings.txt changes)"""
        try:
            if hasattr(self, 'var_crosshair_enabled'):
                # Only update if values actually changed (avoid unnecessary updates)
                if self.var_crosshair_enabled.get() != self.engine.crosshair_enabled:
                    self.var_crosshair_enabled.set(self.engine.crosshair_enabled)
                
                if self.var_crosshair_shape.get() != self.engine.crosshair_shape:
                    self.var_crosshair_shape.set(self.engine.crosshair_shape)
                
                if self.var_crosshair_size.get() != self.engine.crosshair_size:
                    self.var_crosshair_size.set(self.engine.crosshair_size)
                
                if self.var_crosshair_width.get() != self.engine.crosshair_width:
                    self.var_crosshair_width.set(self.engine.crosshair_width)
                
                if self.var_crosshair_locked.get() != self.engine.crosshair_locked:
                    self.var_crosshair_locked.set(self.engine.crosshair_locked)
                
                if self.var_taskbar_visible.get() != self.engine.taskbar_visible:
                    self.var_taskbar_visible.set(self.engine.taskbar_visible)
                
                # If crosshair window exists, redraw with new settings
                if self.crosshair_window.window:
                    self.crosshair_window.draw_crosshair()
        except:
            pass
    
    def sync_popup_with_tab(self):
        """Sync popup controls with tab values"""
        if not hasattr(self, 'crosshair_popup') or not self.crosshair_popup:
            return
        
        try:
            # Update popup controls with current engine values
            # This ensures popup shows same state as tab
            pass  # Popup will update on next redraw
        except:
            pass
    
    def update_color_from_dropdown(self, selection):
        """Handle color dropdown selection"""
        self.engine.crosshair_color = self.color_map.get(selection, '#00ff00')
        if self.crosshair_window.window:
            self.crosshair_window.draw_crosshair()
        self.engine.status = "Crosshair color changed"
    
    def set_crosshair_color(self, color):
        """Set crosshair color"""
        self.engine.crosshair_color = color
        if self.crosshair_window.window:
            self.crosshair_window.draw_crosshair()
        self.engine.status = f"Crosshair color changed"
    
    def toggle_taskbar_visibility(self):
        """Toggle Windows taskbar visibility and save state"""
        try:
            import ctypes
            self.engine.taskbar_visible = self.var_taskbar_visible.get()
            
            # Find and toggle taskbar window
            hwnd = ctypes.windll.user32.FindWindowW("Shell_traywnd", None)
            if hwnd:
                if self.engine.taskbar_visible:
                    # Show taskbar
                    ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW = 5
                    self.engine.status = "Taskbar: VISIBLE"
                else:
                    # Hide taskbar
                    ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
                    self.engine.status = "Taskbar: HIDDEN"
            
            # Save taskbar state to settings.txt
            self.engine.save_taskbar_state()
        except Exception as e:
            self.engine.status = f"Taskbar toggle error: {e}"
    
    def reset_crosshair_position(self):
        """Reset crosshair to center"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.engine.crosshair_x = screen_width // 2
        self.engine.crosshair_y = screen_height // 2
        if self.crosshair_window.window:
            self.crosshair_window.draw_crosshair()
        self.engine.status = "Crosshair reset to center"

    def create_dev_settings_section(self):
        """Developer settings section - NOT USED, using create_dev_tools_tab instead"""
        pass
    
    def create_dev_tools_tab(self):
        """Comprehensive developer tools tab - only called if dev_mode is enabled"""
        if not self.dev_tab_frame:
            return
            
        scroll = tk.Canvas(self.dev_tab_frame, bg='#0d0d0d', highlightthickness=0)
        scroll.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(self.dev_tab_frame, orient='vertical', command=scroll.yview)
        scrollbar.pack(side='right', fill='y')
        
        scroll.configure(yscrollcommand=scrollbar.set)
        frame = tk.Frame(scroll, bg='#0d0d0d')
        scroll.create_window((0, 0), window=frame, anchor='nw')
        
        # Title
        tk.Label(frame, text="DEV MODE SETTINGS", fg='#ff6600', bg='#0d0d0d',
                font=('Arial', 11, 'bold')).pack(pady=5)
        
        # Master enable toggle
        master_frame = tk.Frame(frame, bg='#0d0d0d')
        master_frame.pack(fill='x', pady=3)
        self.var_dev_mode = tk.BooleanVar(value=self.engine.dev_mode)
        tk.Checkbutton(master_frame, text="⚙️ Enable Dev Mode", variable=self.var_dev_mode,
                      bg='#0d0d0d', fg='#ffaa00', selectcolor='#0d0d0d',
                      font=('Arial', 9, 'bold'), command=self.toggle_dev_mode).pack(anchor='w', padx=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=3)
        
        # Logging Section
        tk.Label(frame, text="📋 LOGGING", fg='#00ff00', bg='#0d0d0d',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=3)
        
        self.var_dev_logs = tk.BooleanVar(value=self.engine.dev_logs)
        tk.Checkbutton(frame, text="Enable Console Logs", variable=self.var_dev_logs,
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        self.var_dev_show_keypad = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Keypad Solver Logs", variable=self.var_dev_show_keypad,
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        self.var_dev_show_clicks = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Click Events Logs", variable=self.var_dev_show_clicks,
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=3)
        
        # Display Section
        tk.Label(frame, text="⚡ DISPLAY DEBUG", fg='#00ffff', bg='#0d0d0d',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=3)
        
        self.var_dev_fps = tk.BooleanVar(value=self.engine.dev_show_fps)
        tk.Checkbutton(frame, text="Show FPS Counter", variable=self.var_dev_fps,
                      bg='#0d0d0d', fg='#00ffff', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        self.var_dev_mouse = tk.BooleanVar(value=self.engine.dev_show_mouse_pos)
        tk.Checkbutton(frame, text="Show Mouse Position", variable=self.var_dev_mouse,
                      bg='#0d0d0d', fg='#00ffff', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        self.var_dev_circle_pos = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Show Circle Positions", variable=self.var_dev_circle_pos,
                      bg='#0d0d0d', fg='#00ffff', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=3)
        
        # Debug Section
        tk.Label(frame, text="🔑 HOTKEY DEBUG", fg='#ff00ff', bg='#0d0d0d',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=3)
        
        self.var_dev_hotkey = tk.BooleanVar(value=self.engine.dev_show_hotkey_debug)
        tk.Checkbutton(frame, text="Show Hotkey Presses", variable=self.var_dev_hotkey,
                      bg='#0d0d0d', fg='#ff00ff', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        self.var_dev_key_states = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Show Key States", variable=self.var_dev_key_states,
                      bg='#0d0d0d', fg='#ff00ff', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=3)
        
        # Performance Section
        tk.Label(frame, text="⏱️ PERFORMANCE", fg='#ffff00', bg='#0d0d0d',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=3)
        
        self.var_dev_timings = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Show Operation Timings", variable=self.var_dev_timings,
                      bg='#0d0d0d', fg='#ffff00', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        self.var_dev_memory = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Show Memory Usage", variable=self.var_dev_memory,
                      bg='#0d0d0d', fg='#ffff00', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_dev_settings).pack(anchor='w', padx=20)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=3)
        
        # Fullscreen & Overlay Section
        tk.Label(frame, text="📺 FULLSCREEN OVERLAY", fg='#ffaa00', bg='#0d0d0d',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=3)
        
        self.var_always_on_top = tk.BooleanVar(value=self.engine.dev_always_on_top)
        tk.Checkbutton(frame, text="Always On Top (Over Fullscreen Games)", variable=self.var_always_on_top,
                      bg='#0d0d0d', fg='#ffaa00', selectcolor='#0d0d0d',
                      font=('Arial', 8), command=self.update_fullscreen_settings).pack(anchor='w', padx=20)
        
        transparency_frame = tk.Frame(frame, bg='#0d0d0d')
        transparency_frame.pack(fill='x', padx=20, pady=3)
        tk.Label(transparency_frame, text="Window Transparency:", fg='#ffaa00', bg='#0d0d0d',
                font=('Arial', 8)).pack(side='left')
        
        self.var_window_trans = tk.DoubleVar(value=self.engine.dev_window_transparency)
        trans_slider = tk.Scale(transparency_frame, from_=0.0, to=1.0, resolution=0.05, orient='horizontal',
                               bg='#222', fg='#ffaa00', variable=self.var_window_trans,
                               command=self.update_fullscreen_settings, length=150)
        trans_slider.pack(side='left', padx=5, fill='x', expand=True)
        
        tk.Label(transparency_frame, text="(0=Transparent, 1=Opaque)", fg='#888', bg='#0d0d0d',
                font=('Arial', 7)).pack(side='left', padx=5)
        
        info_fullscreen = """When ZombiU is in fullscreen:
• Python app stays visible above game
• Crosshair remains visible at all times
• App won't hide behind fullscreen window
• Adjust transparency if needed"""
        tk.Label(frame, text=info_fullscreen, fg='#ffaa00', bg='#0d0d0d',
                font=('Courier', 7), justify='left').pack(anchor='w', padx=10, pady=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=3)
        
        # Info Section
        tk.Label(frame, text="ℹ️ VERSION & INFO", fg='#88ff88', bg='#0d0d0d',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=3)
        
        info_text = f"""Version: 1.0
Dev Mode: {'ON' if self.engine.dev_mode else 'OFF'}

All dev tools are logged to console
when enabled. Enable 'Console Logs'
to see detailed debug information.
"""
        tk.Label(frame, text=info_text, fg='#88ff88', bg='#0d0d0d',
                font=('Courier', 8), justify='left').pack(anchor='w', padx=10, pady=5)
        
        # Update scroll region
        frame.update_idletasks()
        scroll.configure(scrollregion=scroll.bbox('all'))
    
    def update_dev_tab_visibility(self):
        """Update dev tab visibility based on dev_mode"""
        if self.engine.dev_mode:
            # Create dev tab if it doesn't exist
            if not hasattr(self, 'dev_tab_frame') or self.dev_tab_frame is None:
                self.dev_tab_frame = tk.Frame(self.content_frame, bg='#0d0d0d')
                self.create_dev_tools_tab()
            
            # Show dev tab button if not exists
            if not hasattr(self, 'btn_tab_dev') or self.btn_tab_dev is None:
                self.btn_tab_dev = tk.Button(self.tab_frame, text="⚙️ DEV TOOLS", bg='#333', fg='#ffaa00',
                                            font=('Arial', 9, 'bold'), cursor='hand2',
                                            command=self.show_dev_tab)
                self.btn_tab_dev.pack(side='left', padx=2, ipadx=10)
        else:
            # Hide dev tab if it exists
            if hasattr(self, 'btn_tab_dev') and self.btn_tab_dev is not None:
                try:
                    self.btn_tab_dev.pack_forget()
                    self.btn_tab_dev.destroy()
                    self.btn_tab_dev = None
                except:
                    pass
            
            if hasattr(self, 'dev_tab_frame') and self.dev_tab_frame is not None:
                try:
                    self.dev_tab_frame.pack_forget()
                    self.dev_tab_frame.destroy()
                    self.dev_tab_frame = None
                except:
                    pass
            
            # Show main tab if dev tab was visible
            self.show_main_tab()

    def open_crosshair_popup(self):
        """Open crosshair menu as popup window on the right side"""
        # Check if popup already exists
        if hasattr(self, 'crosshair_popup') and self.crosshair_popup:
            try:
                self.crosshair_popup.lift()
                self.crosshair_popup.focus()
                return
            except:
                pass
        
        # Hide crosshair tab and show main tab instead
        self.show_main_tab()
        self.btn_tab_crosshair.config(state='disabled', fg='#666')  # Disable crosshair tab button
        
        # Create popup window positioned to the RIGHT of main window
        self.crosshair_popup = tk.Toplevel(self.root)
        self.crosshair_popup.title("⊕ Crosshair Control")
        
        # Make popup always on top and visible
        self.crosshair_popup.attributes('-topmost', True)
        
        # Get main window position and size
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        screen_width = self.root.winfo_screenwidth()
        
        # Position popup to the right of main window (with 20px gap)
        # If in fullscreen, position on the right side of screen
        if self.is_fullscreen:
            popup_x = screen_width - 380  # 350 width + padding
            popup_y = 10
        else:
            popup_x = main_x + main_width + 20
            popup_y = main_y
        
        self.crosshair_popup.geometry(f"350x550+{popup_x}+{popup_y}")
        self.crosshair_popup.config(bg='#0d0d0d')
        self.crosshair_popup.resizable(False, False)
        
        # Build crosshair controls in popup
        frame = tk.Frame(self.crosshair_popup, bg='#0d0d0d')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        tk.Label(frame, text="⊕ CROSSHAIR", fg='#00ffff', bg='#0d0d0d',
                font=('Arial', 11, 'bold')).pack(pady=5)
        
        # Enable
        enable_frame = tk.Frame(frame, bg='#0d0d0d')
        enable_frame.pack(fill='x', pady=3)
        tk.Label(enable_frame, text="Enable:", fg='#888', bg='#0d0d0d').pack(side='left', padx=5)
        var_enable = tk.BooleanVar(value=self.engine.crosshair_enabled)
        tk.Checkbutton(enable_frame, text="ON", variable=var_enable,
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      command=lambda: self.update_popup_crosshair(var_enable, var_shape, var_size, var_width, var_locked)).pack(side='left', padx=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=2)
        
        # Shape
        shape_frame = tk.Frame(frame, bg='#0d0d0d')
        shape_frame.pack(fill='x', pady=3)
        tk.Label(shape_frame, text="Shape:", fg='#888', bg='#0d0d0d').pack(side='left', padx=5)
        var_shape = tk.StringVar(value=self.engine.crosshair_shape)
        shape_menu = tk.OptionMenu(shape_frame, var_shape, 'circle', 'triangle', 'diamond', 'square', 'star', 'cross', 'plus',
                                   'hexagon', 'octagon', 'pentagon', 'x-cross',
                                   command=lambda x: self.update_popup_crosshair(var_enable, var_shape, var_size, var_width, var_locked))
        shape_menu.config(bg='#1a1a1a', fg='#00ff00', activebackground='#333', font=('Arial', 8))
        shape_menu.pack(side='left', padx=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=2)
        
        # Size
        size_frame = tk.Frame(frame, bg='#0d0d0d')
        size_frame.pack(fill='x', pady=3, padx=5)
        tk.Label(size_frame, text="Size:", fg='#888', bg='#0d0d0d', font=('Arial', 8)).pack(side='left', padx=5)
        var_size = tk.IntVar(value=self.engine.crosshair_size)
        tk.Scale(size_frame, from_=5, to=100, variable=var_size, bg='#0d0d0d', fg='#00ff00',
                orient=tk.HORIZONTAL, font=('Arial', 7), command=lambda x: self.update_popup_crosshair(var_enable, var_shape, var_size, var_width, var_locked)).pack(side='left', padx=5, fill=tk.X, expand=True)
        
        # Bold (line width)
        width_frame = tk.Frame(frame, bg='#0d0d0d')
        width_frame.pack(fill='x', pady=3, padx=5)
        tk.Label(width_frame, text="Bold:", fg='#888', bg='#0d0d0d', font=('Arial', 8)).pack(side='left', padx=5)
        var_width = tk.IntVar(value=self.engine.crosshair_width)
        tk.Scale(width_frame, from_=1, to=8, variable=var_width, bg='#0d0d0d', fg='#00ff00',
                orient=tk.HORIZONTAL, font=('Arial', 7), command=lambda x: self.update_popup_crosshair(var_enable, var_shape, var_size, var_width, var_locked)).pack(side='left', padx=5, fill=tk.X, expand=True)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=2)
        
        # Colors
        tk.Label(frame, text="Color:", fg='#888', bg='#0d0d0d', font=('Arial', 8)).pack(anchor='w', padx=10, pady=2)
        color_f1 = tk.Frame(frame, bg='#0d0d0d')
        color_f1.pack(fill='x', padx=10, pady=1)
        for color, name in [('#00ff00', 'G'), ('#ff0000', 'R'), ('#0000ff', 'B'), ('#ffff00', 'Y')]:
            tk.Button(color_f1, text=name, bg=color, fg='#000', width=3, font=('Arial', 7),
                     command=lambda c=color: self.set_popup_color(c)).pack(side='left', padx=1)
        
        color_f2 = tk.Frame(frame, bg='#0d0d0d')
        color_f2.pack(fill='x', padx=10, pady=1)
        for color, name in [('#ff00ff', 'M'), ('#00ffff', 'C')]:
            tk.Button(color_f2, text=name, bg=color, fg='#000', width=3, font=('Arial', 7),
                     command=lambda c=color: self.set_popup_color(c)).pack(side='left', padx=1)
        tk.Button(color_f2, text="Custom", bg='#444', fg='#fff', font=('Arial', 7),
                 command=self.pick_custom_color).pack(side='left', padx=1)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=2)
        
        # Lock
        lock_frame = tk.Frame(frame, bg='#0d0d0d')
        lock_frame.pack(fill='x', pady=3)
        tk.Label(lock_frame, text="Locked:", fg='#888', bg='#0d0d0d', font=('Arial', 8)).pack(side='left', padx=5)
        var_locked = tk.BooleanVar(value=self.engine.crosshair_locked)
        tk.Checkbutton(lock_frame, text="Yes", variable=var_locked, font=('Arial', 8),
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      command=lambda: self.update_popup_crosshair(var_enable, var_shape, var_size, var_width, var_locked)).pack(side='left', padx=5)
        
        tk.Frame(frame, height=1, bg='#333').pack(fill='x', pady=2)
        
        # Taskbar visibility
        taskbar_frame = tk.Frame(frame, bg='#0d0d0d')
        taskbar_frame.pack(fill='x', pady=3)
        tk.Label(taskbar_frame, text="Taskbar:", fg='#888', bg='#0d0d0d', font=('Arial', 8)).pack(side='left', padx=5)
        var_taskbar = tk.BooleanVar(value=self.engine.taskbar_visible)
        tk.Checkbutton(taskbar_frame, text="Show", variable=var_taskbar, font=('Arial', 8),
                      bg='#0d0d0d', fg='#00ff00', selectcolor='#0d0d0d',
                      command=lambda: self.toggle_taskbar_visibility_from_popup(var_taskbar)).pack(side='left', padx=5)
        
        # Reset
        tk.Button(frame, text="Reset to Center", bg='#2a5', fg='white', font=('Arial', 8),
                 command=self.reset_crosshair_position).pack(pady=5)
        
        # Handle window close
        self.crosshair_popup.protocol("WM_DELETE_WINDOW", lambda: self.close_crosshair_popup())
    
    def update_popup_crosshair(self, var_enable, var_shape, var_size, var_width, var_locked):
        """Update crosshair from popup values and sync with tab"""
        self.engine.crosshair_enabled = var_enable.get()
        self.engine.crosshair_shape = var_shape.get()
        self.engine.crosshair_size = var_size.get()
        self.engine.crosshair_width = var_width.get()
        self.engine.crosshair_locked = var_locked.get()
        
        # Show/Hide crosshair based on enabled state
        if self.engine.crosshair_enabled:
            # Crosshair ENABLED - show it
            if not self.crosshair_window.window:
                self.crosshair_window.show()
            self.crosshair_window.draw_crosshair()
        else:
            # Crosshair DISABLED - hide it completely
            self.crosshair_window.hide()
        
        # Sync tab controls with popup values
        if hasattr(self, 'var_crosshair_enabled'):
            self.var_crosshair_enabled.set(var_enable.get())
            self.var_crosshair_shape.set(var_shape.get())
            self.var_crosshair_size.set(var_size.get())
            self.var_crosshair_width.set(var_width.get())
            self.var_crosshair_locked.set(var_locked.get())
        
        status_text = "Crosshair: ON ✓" if self.engine.crosshair_enabled else "Crosshair: OFF"
        self.engine.status = status_text
    
    def toggle_taskbar_visibility_from_popup(self, var_taskbar):
        """Toggle taskbar from popup and save state"""
        self.engine.taskbar_visible = var_taskbar.get()
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW("Shell_traywnd", None)
            if hwnd:
                if self.engine.taskbar_visible:
                    ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW = 5
                    self.engine.status = "Taskbar: VISIBLE"
                else:
                    ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
                    self.engine.status = "Taskbar: HIDDEN"
        except Exception as e:
            self.engine.status = f"Taskbar toggle error: {e}"
        
        # Save taskbar state to settings.txt
        self.engine.save_taskbar_state()
    
    def set_popup_color(self, color):
        """Set color from popup"""
        self.engine.crosshair_color = color
        if self.crosshair_window.window:
            self.crosshair_window.draw_crosshair()
    
    def close_crosshair_popup(self):
        """Close crosshair popup and re-enable crosshair tab button"""
        if hasattr(self, 'crosshair_popup') and self.crosshair_popup:
            try:
                self.crosshair_popup.destroy()
            except:
                pass
            self.crosshair_popup = None
        
        # Re-enable crosshair tab button
        self.btn_tab_crosshair.config(state='normal', fg='#00ff00')
    
    def show_main_tab(self):
        """Show main tab - thread safe"""
        try:
            self.main_tab_frame.pack(fill='both', expand=True)
            self.crosshair_tab_frame.pack_forget()
            if self.dev_tab_frame:
                self.dev_tab_frame.pack_forget()
            self.btn_tab_main.config(bg='#00ff00', fg='#000')
            self.btn_tab_crosshair.config(bg='#333', fg='#00ff00')
            if self.btn_tab_dev:
                self.btn_tab_dev.config(bg='#333', fg='#ffaa00')
        except Exception as e:
            print(f"[ERROR] show_main_tab: {e}")
    
    def show_crosshair_tab(self):
        """Show crosshair tab - thread safe"""
        try:
            self.main_tab_frame.pack_forget()
            self.crosshair_tab_frame.pack(fill='both', expand=True)
            if self.dev_tab_frame:
                self.dev_tab_frame.pack_forget()
            self.btn_tab_main.config(bg='#333', fg='#00ff00')
            self.btn_tab_crosshair.config(bg='#00ffff', fg='#000')
            if self.btn_tab_dev:
                self.btn_tab_dev.config(bg='#333', fg='#ffaa00')
        except Exception as e:
            print(f"[ERROR] show_crosshair_tab: {e}")
    
    def pick_custom_color(self):
        """Open color picker dialog"""
        try:
            from tkinter.colorchooser import askcolor
            color = askcolor(color=self.engine.crosshair_color, title="Choose Crosshair Color")
            if color[1]:  # color[1] is the hex value
                self.set_crosshair_color(color[1])
        except:
            self.engine.status = "Color picker not available"
    
    def show_dev_tab(self):
        """Show dev tab - thread safe"""
        try:
            if self.dev_tab_frame:
                self.main_tab_frame.pack_forget()
                self.crosshair_tab_frame.pack_forget()
                self.dev_tab_frame.pack(fill='both', expand=True)
                self.btn_tab_main.config(bg='#333', fg='#00ff00')
                self.btn_tab_crosshair.config(bg='#333', fg='#00ff00')
                if self.btn_tab_dev:
                    self.btn_tab_dev.config(bg='#ff6600', fg='#000')
        except Exception as e:
            print(f"[ERROR] show_dev_tab: {e}")
    
    def toggle_dev_mode(self):
        """Toggle dev mode on/off"""
        self.engine.dev_mode = self.var_dev_mode.get()
        self.engine.status = f"Dev Mode {'ON ✓' if self.engine.dev_mode else 'OFF'}"
        if self.engine.dev_logs:
            print(f"[DEV] Dev mode {'ENABLED' if self.engine.dev_mode else 'DISABLED'}")
    
    def update_dev_mode_display(self):
        """Placeholder for compatibility"""
        pass
    
    def update_dev_settings(self):
        """Update engine dev settings from GUI - ALL checkboxes now work!"""
        # Update ALL dev settings from checkboxes
        self.engine.dev_logs = self.var_dev_logs.get()
        self.engine.dev_show_fps = self.var_dev_fps.get()
        self.engine.dev_show_mouse_pos = self.var_dev_mouse.get()
        self.engine.dev_show_hotkey_debug = self.var_dev_hotkey.get()
        
        # Print status if console logs enabled
        if self.engine.dev_logs:
            status = "["
            status += f"Logs:{'ON' if self.var_dev_logs.get() else 'OFF'} | "
            status += f"FPS:{'ON' if self.var_dev_fps.get() else 'OFF'} | "
            status += f"Mouse:{'ON' if self.var_dev_mouse.get() else 'OFF'} | "
            status += f"Hotkey:{'ON' if self.var_dev_hotkey.get() else 'OFF'} | "
            status += f"Keypad:{'ON' if self.var_dev_show_keypad.get() else 'OFF'} | "
            status += f"Clicks:{'ON' if self.var_dev_show_clicks.get() else 'OFF'} | "
            status += f"Circles:{'ON' if self.var_dev_circle_pos.get() else 'OFF'} | "
            status += f"Keys:{'ON' if self.var_dev_key_states.get() else 'OFF'} | "
            status += f"Timings:{'ON' if self.var_dev_timings.get() else 'OFF'} | "
            status += f"Memory:{'ON' if self.var_dev_memory.get() else 'OFF'}]"
            print(f"[DEV] {status}")
            self.engine.status = f"✓ {status}"
        else:
            self.engine.status = "Dev settings updated"

    def update_fullscreen_settings(self, *args):
        """Update fullscreen overlay settings"""
        self.engine.dev_always_on_top = self.var_always_on_top.get()
        self.engine.dev_window_transparency = self.var_window_trans.get()
        
        # Apply always on top to main window
        try:
            self.root.attributes('-topmost', self.engine.dev_always_on_top)
        except:
            pass
        
        # Apply transparency
        try:
            self.root.attributes('-alpha', self.engine.dev_window_transparency)
        except:
            pass
        
        if self.engine.dev_logs:
            print(f"[DEV] Fullscreen settings updated - Always on top: {self.engine.dev_always_on_top}, Transparency: {self.engine.dev_window_transparency:.2f}")
        
        self.engine.status = f"Window: Always-on-top={'ON' if self.engine.dev_always_on_top else 'OFF'}, Transparency={self.engine.dev_window_transparency:.1%}"

    def save_original_taskbar_state(self):
        """Save the original Windows taskbar state (before app modifies it)"""
        try:
            import ctypes
            import winreg
            
            # Check Windows Registry for taskbar auto-hide setting
            # If value doesn't exist or error, we'll just remember current visible state
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                    r'Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3')
                value, regtype = winreg.QueryValueEx(key, 'Settings')
                # Byte 8 indicates auto-hide: 1=auto-hide on, 0=auto-hide off
                self.original_taskbar_state = 'auto-hide' if (value[8] & 0x01) else 'visible'
                winreg.CloseKey(key)
            except:
                # Fallback: check if taskbar window is visible
                hwnd = ctypes.windll.user32.FindWindowW("Shell_traywnd", None)
                if hwnd:
                    is_visible = ctypes.windll.user32.IsWindowVisible(hwnd)
                    self.original_taskbar_state = 'visible' if is_visible else 'hidden'
                else:
                    self.original_taskbar_state = 'visible'
        except:
            self.original_taskbar_state = 'visible'

    def apply_saved_taskbar_state(self):
        """Apply saved taskbar state on startup"""
        try:
            import ctypes
            if self.engine.taskbar_visible:
                # Show taskbar
                hwnd = ctypes.windll.user32.FindWindowW("Shell_traywnd", None)
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW = 5
            else:
                # Hide taskbar
                hwnd = ctypes.windll.user32.FindWindowW("Shell_traywnd", None)
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
        except:
            pass

    def update_keybind_labels(self):
        """Update keybind labels to show current keybind from settings"""
        # Reload keybinds from settings every frame
        self.engine.load_settings()
        
        # Convert hex codes to key names
        keybind_map = {
            0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4", 0x74: "F5", 0x75: "F6",
            0x76: "F7", 0x77: "F8", 0x78: "F9", 0x79: "F10", 0x7A: "F11", 0x7B: "F12",
            0x41: "A", 0x42: "B", 0x43: "C", 0x44: "D", 0x45: "E", 0x46: "F", 0x47: "G",
            0x48: "H", 0x49: "I", 0x4A: "J", 0x4B: "K", 0x4C: "L", 0x4D: "M", 0x4E: "N",
            0x4F: "O", 0x50: "P", 0x51: "Q", 0x52: "R", 0x53: "S", 0x54: "T", 0x55: "U",
            0x56: "V", 0x57: "W", 0x58: "X", 0x59: "Y", 0x5A: "Z",
            0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3", 0x34: "4", 0x35: "5",
            0x36: "6", 0x37: "7", 0x38: "8", 0x39: "9",
            0xA0: "LSHIFT", 0xA1: "RSHIFT", 0xA2: "LCTRL", 0xA3: "RCTRL",
            0xA4: "LALT", 0xA5: "RALT", 0x20: "SPACE", 0x0D: "ENTER"
        }
        
        f1_name = keybind_map.get(self.engine.keybind_f1, f"0x{self.engine.keybind_f1:x}")
        f3_name = keybind_map.get(self.engine.keybind_f3, f"0x{self.engine.keybind_f3:x}")
        f4_name = keybind_map.get(self.engine.keybind_f4, f"0x{self.engine.keybind_f4:x}")
        
        if hasattr(self, 'lbl_f1_keybind'):
            self.lbl_f1_keybind.config(text=f"{f1_name}: KEYPAD SOLVER")
        if hasattr(self, 'lbl_f3_keybind'):
            self.lbl_f3_keybind.config(text=f"{f3_name}: SPEEDRUN TIMER")
        if hasattr(self, 'lbl_f4_keybind'):
            self.lbl_f4_keybind.config(text=f"{f4_name}: COMBINED MODE")
    
    def apply_theme_to_gui(self):
        """Apply the engine's theme colors to GUI elements"""
        try:
            # Apply to main frame border
            self.main_frame.config(highlightbackground=self.engine.hud_border_color)
            
            # For modern2026 theme, apply additional styling
            if self.engine.hud_theme == 'modern2026':
                # Use raised relief for modern look
                self.main_frame.config(relief='raised', bd=2)
                # Apply light padding to content
                self.content_frame.config(padx=3, pady=3)
            
            # Apply to status label
            self.lbl_status.config(fg=self.engine.hud_text_color, bg=self.engine.hud_bg_color)
            
            # Apply to keypad labels and displays
            if hasattr(self, 'lbl_f1_keybind'):
                self.lbl_f1_keybind.config(fg=self.engine.hud_text_color, bg=self.engine.hud_bg_color)
            if hasattr(self, 'lbl_keypad'):
                self.lbl_keypad.config(fg=self.engine.hud_text_color, bg=self.engine.hud_bg_color)
            if hasattr(self, 'lbl_last_code'):
                self.lbl_last_code.config(fg=self.engine.hud_text_color, bg=self.engine.hud_bg_color)
            if hasattr(self, 'lbl_found'):
                self.lbl_found.config(fg=self.engine.hud_text_color, bg=self.engine.hud_bg_color)
            
            # Apply to timer label
            if hasattr(self, 'lbl_f3_keybind'):
                self.lbl_f3_keybind.config(fg=self.engine.hud_text_color, bg=self.engine.hud_bg_color)
            if hasattr(self, 'lbl_timer'):
                self.lbl_timer.config(fg=self.engine.hud_text_color, bg=self.engine.hud_bg_color)
            
            # Apply to f2 label
            if hasattr(self, 'lbl_f2_keybind'):
                self.lbl_f2_keybind.config(fg=self.engine.hud_text_color, bg=self.engine.hud_bg_color)
            
            # Apply to f4 label
            if hasattr(self, 'lbl_f4_keybind'):
                self.lbl_f4_keybind.config(fg=self.engine.hud_text_color, bg=self.engine.hud_bg_color)
                
            # Apply modern styling to all frames if modern2026 theme
            if self.engine.hud_theme == 'modern2026':
                self.apply_modern_frame_styling()
        except:
            pass
    
    def apply_modern_frame_styling(self):
        """Apply modern 2026 styling to frames for cleaner look"""
        try:
            # Get all frame widgets and apply modern styling
            modern_relief = 'flat'
            modern_bg = self.engine.hud_bg_color
            
            # Apply to tab buttons - modern flat design with subtle colors
            if hasattr(self, 'btn_tab_main'):
                self.btn_tab_main.config(relief='flat', bd=0, bg='#1a1a1e', activebackground='#00d4ff', 
                                         fg='#e0e0e0', activeforeground='#000', font=('Arial', 9, 'bold'))
            if hasattr(self, 'btn_tab_crosshair'):
                self.btn_tab_crosshair.config(relief='flat', bd=0, bg='#1a1a1e', activebackground='#00d4ff',
                                               fg='#e0e0e0', activeforeground='#000', font=('Arial', 9, 'bold'))
            if hasattr(self, 'btn_tab_dev'):
                if self.btn_tab_dev:
                    self.btn_tab_dev.config(relief='flat', bd=0, bg='#1a1a1e', activebackground='#00d4ff',
                                            fg='#ffaa00', activeforeground='#000', font=('Arial', 9, 'bold'))
            
            # Apply to key blocker buttons - flat with subtle styling
            for key in self.engine.available_keys:
                btn_name = f'btn_{key}'
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    btn.config(relief='flat', bd=0, padx=2, pady=2, bg='#1a1a1e', 
                              fg='#e0e0e0', activebackground='#00d4ff', activeforeground='#000')
            
            # Apply to action buttons
            for btn_name in ['btn_all_keys', 'btn_reset_keypad', 'btn_place_circles']:
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    btn.config(relief='flat', bd=0, bg='#1a1a1e', fg='#e0e0e0',
                              activebackground='#00d4ff', activeforeground='#000')
                    
        except Exception as e:
            pass
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        try:
            self.is_fullscreen = not getattr(self, 'is_fullscreen', False)
            
            if self.is_fullscreen:
                # Store current position/size before fullscreen
                self.saved_geometry = self.root.geometry()
                # Make fullscreen
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
                self.engine.status = "FULLSCREEN MODE"
            else:
                # Restore previous geometry
                if hasattr(self, 'saved_geometry'):
                    self.root.geometry(self.saved_geometry)
                else:
                    self.root.geometry("450x900+50+50")
                self.engine.status = "Window Mode"
        except Exception as e:
            self.engine.status = f"Fullscreen error: {e}"
    
    def minimize(self):
        self.root.withdraw()
        self.root.after(3000, self.root.deiconify)

    def update(self):
        try:
            # Check if dev_mode changed in settings.txt (reload settings)
            try:
                self.engine.load_settings()
            except:
                pass
            
            if self.last_dev_mode != self.engine.dev_mode:
                self.last_dev_mode = self.engine.dev_mode
                try:
                    self.update_dev_tab_visibility()
                except:
                    pass
            
            # Sync crosshair settings from engine to UI controls if they changed
            try:
                self.sync_crosshair_ui_from_engine()
            except:
                pass
            
            # Update dev checkboxes if they exist
            try:
                if hasattr(self, 'var_dev_logs'):
                    self.engine.dev_logs = self.var_dev_logs.get()
                if hasattr(self, 'var_dev_fps'):
                    self.engine.dev_show_fps = self.var_dev_fps.get()
                if hasattr(self, 'var_dev_mouse'):
                    self.engine.dev_show_mouse_pos = self.var_dev_mouse.get()
                if hasattr(self, 'var_dev_hotkey'):
                    self.engine.dev_show_hotkey_debug = self.var_dev_hotkey.get()
            except:
                pass
            
            try:
                self.lbl_status.config(text=self.engine.status)
                if "✓" in self.engine.status or "DETECTED" in self.engine.status:
                    self.lbl_status.config(fg='#00ff00')
                elif "Waiting" in self.engine.status:
                    self.lbl_status.config(fg='#ffff00')
                elif "Solving" in self.engine.status or "Trying" in self.engine.status or "Clicking" in self.engine.status or "Starting" in self.engine.status:
                    self.lbl_status.config(fg='#ff8800')
                else:
                    self.lbl_status.config(fg='#00ffff')
            except:
                pass
            
            try:
                if self.engine.keypad_code:
                    self.lbl_keypad.config(text=f"Code: {self.engine.keypad_code}")
            except:
                pass
            
            try:
                if self.engine.last_successful_code:
                    self.lbl_last_code.config(text=f"Last Good Code: {self.engine.last_successful_code}",
                                             fg='#00ff00')
                else:
                    self.lbl_last_code.config(text="Last Good Code: None", fg='#ffaa00')
            except:
                pass
            
            try:
                self.update_found_codes()
            except:
                pass
            
            try:
                timer_text = self.engine.get_timer_display()
                self.lbl_timer.config(text=timer_text)
                
                if self.engine.timer_active and not self.engine.timer_paused:
                    self.lbl_timer.config(fg='#00ff00')
                elif self.engine.timer_paused:
                    self.lbl_timer.config(fg='#ffff00')
                else:
                    self.lbl_timer.config(fg='#00ffff')
            except:
                pass
            
            # Disable buttons ONLY during countdown or auto-clicker
            try:
                if (self.engine.autostart_timer_running or 
                    self.engine.auto_clicking):
                    self.btn_place_circles.config(state='disabled', bg='#666', fg='#888')
                    self.btn_reset_keypad.config(state='disabled', bg='#666', fg='#888')
                else:
                    self.btn_place_circles.config(state='normal', bg='#2a2', fg='white')
                    self.btn_reset_keypad.config(state='normal', bg='#a52', fg='white')
            except:
                pass
            
        except Exception as e:
            print(f"[ERROR] in update loop: {e}")
        
        try:
            self.update_keybind_labels()
            self.apply_theme_to_gui()
        except:
            pass
        
        try:
            if ctypes.windll.user32.GetAsyncKeyState(self.engine.keybind_f1) & 0x8000:  # F1
                # Stop auto-clicker if running
                if self.engine.auto_clicking:
                    self.engine.auto_clicking = False
                    self.engine.status = "F1 PRESSED - AUTO-CLICKER STOPPED!"
                # Stop countdown if running
                if self.engine.autostart_timer_running:
                    self.engine.autostart_timer_running = False
                    self.engine.circle_ready = False
                    self.engine.status = "F1 PRESSED - AUTOSTART TIMER CANCELLED!"
            if ctypes.windll.user32.GetAsyncKeyState(self.engine.keybind_f3) & 1: # F3
                self.engine.toggle_timer()
        except:
            pass
        
        self.root.after(50, self.update)

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def on_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def close_app(self):
        """Close app and cleanup all windows properly"""
        try:
            # Stop engine first
            self.engine.stop()
        except:
            pass
        
        try:
            # Close circle placer window if exists
            if hasattr(self, 'circle_placer') and self.circle_placer:
                try:
                    if hasattr(self.circle_placer, 'window') and self.circle_placer.window:
                        self.circle_placer.hide()
                except:
                    pass
        except:
            pass
        
        try:
            # Destroy main root window
            self.root.destroy()
        except:
            pass
    
    def on_closing(self):
        """Close app - do NOT modify taskbar"""
        self.engine.save_keypad_resume()
        self.engine.save_blocked_keys()
        self.close_app()

# ==============================================================================
# MAIN ENTRY
# ==============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("""
███████╗ ██████╗ ███╗   ███╗██████╗ ██╗    ████████╗ ██████╗  ██████╗ ██╗     ███████╗
╚══███╔╝██╔═══██╗████╗ ████║██╔══██╗██║    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝
  ███╔╝ ██║   ██║██╔████╔██║██████╔╝██║       ██║   ██║   ██║██║   ██║██║     ███████╗
 ███╔╝  ██║   ██║██║╚██╔╝██║██╔══██╗██║       ██║   ██║   ██║██║   ██║██║     ╚════██║
███████╗╚██████╔╝██║ ╚═╝ ██║██████╔╝██║       ██║   ╚██████╔╝╚██████╔╝███████╗███████║
╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═════╝ ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝
    """)
    print("                            VERSION 1.0")
    print("=" * 80)
    
    print("\nQUICK START:")
    print("-" * 80)
    print("1. Open keypad in game")
    print("2. Click 'Place Circles & Auto-Start'")
    print("3. Double-click X for see-through mode")
    print("4. Hold X + Click on buttons (1-9, 0, ENTER, X)")
    print("5. Wait 10 sec, auto-clicker starts")
    print("6. F1 to close/stop")
    print("-" * 80)
    
    print("\nCONTROLS:")
    print("-" * 80)
    print("Double-click X  = See-through mode")
    print("Hold X + Click  = Place circle")
    print("F1              = Close overlay / Stop clicker")
    print("-" * 80)
    
    print("\nCUSTOMIZATION:")
    print("-" * 80)
    print("Edit settings.txt to customize:")
    print("  - Speed: click_delay, enter_delay (0.1 = ULTRA FAST)")
    print("  - HUD Themes: default, military, alpha, rounded, minimal")
    print("  - HUD Colors: background, text, border (hex format)")
    print("  - HUD Style: corner_radius, border_width")
    print("  - Sounds: beep_countdown, beep_placement")
    print("Settings.txt created automatically on first run")
    print("-" * 80)
    
    print("\nHOTKEYS:")
    print("-" * 80)
    print("Ctrl+Z  = Undo last circle")
    print("Ctrl+Y  = Redo last circle")
    print("Ctrl+R  = Reset all circles")
    print("F1      = Close overlay / Stop clicker")
    print("-" * 80)
    
    # GitHub Logo (Small ASCII)
    print("\n  github_logo")
    print("  Creator: NYC0DEV")
    print("  GitHub: https://github.com/NYC0DEV")
    print("  Settings loaded from settings.txt")
    print("=" * 80)
    
    # Create trainer first to get app_folder
    trainer = ZombiUTrainer()
    
    # SINGLE INSTANCE LOCK - Prevent multiple app openings
    lock_file = os.path.join(trainer.app_folder, '.zombi_lock')
    
    # Check if app is already running
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                old_pid = int(f.read().strip())
            # Check if process is still alive
            if psutil.pid_exists(old_pid):
                print("\n" + "=" * 80)
                print("ERROR: Zombi Tools is ALREADY RUNNING!")
                print("=" * 80)
                print("You can only run ONE instance at a time.")
                print("Close the existing window and try again.")
                print("=" * 80 + "\n")
                import sys
                sys.exit(1)
            else:
                # Old process dead, remove old lock
                try:
                    os.remove(lock_file)
                except:
                    pass
        except:
            pass
    
    # Create lock file with current process ID
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass
    
    try:
        # Verify files were created
        print("\n" + "="*80)
        settings_file = os.path.join(trainer.app_folder, 'settings.txt')
        keypad_file = os.path.join(trainer.app_folder, 'keypad_resume.txt')
        keys_file = os.path.join(trainer.app_folder, 'keys.txt')
        
        if os.path.exists(settings_file):
            print(f"✓ settings.txt created")
        else:
            print(f"✗ settings.txt NOT created")
            
        if os.path.exists(keypad_file):
            print(f"✓ keypad_resume.txt created")
        else:
            print(f"✗ keypad_resume.txt NOT created")
            
        if os.path.exists(keys_file):
            print(f"✓ keys.txt created")
        else:
            print(f"✗ keys.txt NOT created")
        print("="*80 + "\n")
        
        Thread(target=trainer.check_game_running, daemon=True).start()
        
        gui = TrainerGUI(trainer)
        gui.root.mainloop()
    finally:
        # Remove lock file when app closes
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except:
            pass