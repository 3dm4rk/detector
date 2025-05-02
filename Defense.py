import psutil
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
import time
import json
import atexit
import winsound
from pygame import mixer

class AppMonitorGUI:
    CONFIG_FILE = "app_monitor_config.json"
    ALERT_SOUND = "alert.wav"
    
    def __init__(self, root):
        self.root = root
        self.root.title("Application Monitor")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Initialize sound mixer
        mixer.init()
        
        # Variables
        self.monitoring = False
        self.app_name = tk.StringVar()
        self.max_instances = tk.IntVar(value=1)
        self.hide_window = tk.BooleanVar(value=False)
        self.start_hidden = tk.BooleanVar(value=False)
        self.play_sound = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Status: Ready")
        self.warning_shown = False
        
        # Load configuration
        self.load_config()
        
        # GUI Elements
        self.create_widgets()
        
        # Register cleanup
        atexit.register(self.cleanup)
        
        # Start hidden if configured
        if self.start_hidden.get() and not self.is_already_running():
            self.start_monitoring(silent=True)
    
    def load_config(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.app_name.set(config.get('app_name', ''))
                    self.max_instances.set(config.get('max_instances', 1))
                    self.hide_window.set(config.get('hide_window', False))
                    self.start_hidden.set(config.get('start_hidden', False))
                    self.play_sound.set(config.get('play_sound', True))
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        try:
            config = {
                'app_name': self.app_name.get(),
                'max_instances': self.max_instances.get(),
                'hide_window': self.hide_window.get(),
                'start_hidden': self.start_hidden.get(),
                'play_sound': self.play_sound.get()
            }
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def cleanup(self):
        self.save_config()
        if self.monitoring:
            self.stop_monitoring()
        mixer.quit()
    
    def play_alert_sound(self):
        if not self.play_sound.get():
            return
            
        try:
            winsound.PlaySound(self.ALERT_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:
            try:
                mixer.music.load(self.ALERT_SOUND)
                mixer.music.play()
            except Exception as e:
                print(f"Error playing sound: {e}")
    
    def show_warning_popup(self, app_name, current_instances):
        if self.warning_shown:
            return
            
        self.warning_shown = True
        self.play_alert_sound()
        
        warning_root = tk.Toplevel(self.root)
        warning_root.title("WARNING")
        warning_root.attributes('-fullscreen', True)
        warning_root.configure(bg='red')
        warning_root.overrideredirect(True)
        warning_root.attributes('-topmost', True)
        
        # Main warning frame
        warning_frame = tk.Frame(warning_root, bg='red')
        warning_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Custom warning message
        text_lines = [
            "SAKPAN NAKA AYAW PANIKAS!",
            "",
            "KLARO KAAYO KA SA CCTV",
            "OG MAKITA NAKO SA IMONG SCREEN",
            "KUNG UNSA IMO GI BUHAT!"
        ]
        
        for i, line in enumerate(text_lines):
            font_size = 48 if i == 0 else 36
            tk.Label(warning_frame, 
                    text=line,
                    font=('Arial', font_size, 'bold'),
                    bg='red',
                    fg='white').pack(expand=(i==0), pady=(10 if i==0 else 5))
        
        # Close button
        close_btn = tk.Button(warning_frame,
                            text="CLOSE WARNING",
                            command=lambda: self.close_warning(warning_root),
                            font=('Arial', 24, 'bold'),
                            bg='white',
                            fg='red',
                            bd=5,
                            relief=tk.RAISED,
                            padx=20,
                            pady=10)
        close_btn.pack(pady=30)
        
        if self.hide_window.get():
            self.root.deiconify()
        
        warning_root.grab_set()
    
    def close_warning(self, window):
        self.warning_shown = False
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except:
            mixer.music.stop()
        window.destroy()
        if self.hide_window.get() and self.monitoring:
            self.root.withdraw()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="Application Monitor", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Application entry
        app_frame = ttk.Frame(main_frame)
        app_frame.pack(fill=tk.X, pady=5)
        ttk.Label(app_frame, text="Application to monitor:").pack(side=tk.LEFT)
        self.app_entry = ttk.Entry(app_frame, textvariable=self.app_name, width=25)
        self.app_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(app_frame, text=".exe").pack(side=tk.LEFT)
        
        # Max instances
        instances_frame = ttk.Frame(main_frame)
        instances_frame.pack(fill=tk.X, pady=5)
        ttk.Label(instances_frame, text="Max allowed instances:").pack(side=tk.LEFT)
        self.instances_spin = ttk.Spinbox(instances_frame, from_=1, to=10, textvariable=self.max_instances, width=5)
        self.instances_spin.pack(side=tk.LEFT, padx=5)
        
        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(options_frame, text="Hide window when monitoring", variable=self.hide_window).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Start hidden on next launch", variable=self.start_hidden).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Play alert sound", variable=self.play_sound).pack(anchor=tk.W)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        self.start_btn = ttk.Button(btn_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        ttk.Label(status_frame, textvariable=self.status_text, font=('Arial', 10)).pack()
    
    def get_app_processes(self, app_name):
        matching_processes = []
        for process in psutil.process_iter(['name']):
            try:
                if process.info['name'].lower() == app_name.lower():
                    matching_processes.append(process)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return matching_processes
    
    def start_monitoring(self, silent=False):
        app_name = self.app_name.get().strip()
        if not app_name and not silent:
            messagebox.showwarning("Warning", "Please enter an application name")
            return
        
        if not app_name.lower().endswith('.exe'):
            app_name += '.exe'
            self.app_name.set(app_name)
        
        max_instances = self.max_instances.get()
        
        self.monitoring = True
        self.warning_shown = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.app_entry.config(state=tk.DISABLED)
        self.instances_spin.config(state=tk.DISABLED)
        self.status_text.set(f"Monitoring: {app_name} (Max {max_instances} instances)")
        self.save_config()
        
        if self.hide_window.get():
            self.root.withdraw()
        
        self.monitor_thread = threading.Thread(
            target=self.monitor_application,
            args=(app_name, max_instances),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.app_entry.config(state=tk.NORMAL)
        self.instances_spin.config(state=tk.NORMAL)
        self.status_text.set("Status: Monitoring stopped")
        self.root.deiconify()
        self.save_config()
    
    def monitor_application(self, app_name, max_instances):
        while self.monitoring:
            processes = self.get_app_processes(app_name)
            num_processes = len(processes)
            
            if num_processes > max_instances and not self.warning_shown:
                self.root.after(0, lambda: self.show_warning_popup(app_name, num_processes))
            
            time.sleep(1)
    
    def on_closing(self):
        if self.monitoring:
            if messagebox.askokcancel("Quit", "Monitoring is active. Are you sure you want to quit?"):
                self.cleanup()
                self.root.destroy()
        else:
            self.cleanup()
            self.root.destroy()
    
    def is_already_running(self):
        current_pid = os.getpid()
        current_name = os.path.basename(sys.argv[0]).lower()
        
        for process in psutil.process_iter(['pid', 'name']):
            try:
                process_name = process.info['name'].lower()
                if (process.info['pid'] != current_pid and 
                    (process_name == current_name or 
                     (process_name == 'python.exe' and 
                      any(arg.lower() == current_name for arg in process.cmdline()[1:])))):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

if __name__ == "__main__":
    def check_already_running():
        current_pid = os.getpid()
        current_name = os.path.basename(sys.argv[0]).lower()
        
        for process in psutil.process_iter(['pid', 'name']):
            try:
                process_name = process.info['name'].lower()
                if (process.info['pid'] != current_pid and 
                    (process_name == current_name or 
                     (process_name == 'python.exe' and 
                      any(arg.lower() == current_name for arg in process.cmdline()[1:])))):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    if check_already_running():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", "The application monitor is already running!")
        sys.exit(1)
    
    root = tk.Tk()
    app = AppMonitorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
