import os
import psutil
import time
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import threading

class AppMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Application Monitor")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        
        # Variables
        self.monitoring = False
        self.app_name = tk.StringVar()
        self.status_text = tk.StringVar(value="Status: Ready")
        
        # GUI Elements
        self.create_widgets()
        
        # Check for admin rights
        if not self.is_admin():
            messagebox.showwarning("Warning", "This program requires administrator privileges to shutdown the computer.\nPlease run as administrator.")
    
    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Application Monitor", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Application name entry
        app_frame = ttk.Frame(main_frame)
        app_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(app_frame, text="Application to monitor:").pack(side=tk.LEFT)
        self.app_entry = ttk.Entry(app_frame, textvariable=self.app_name, width=25)
        self.app_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(app_frame, text=".exe").pack(side=tk.LEFT)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        self.start_btn = ttk.Button(btn_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, textvariable=self.status_text, font=('Arial', 10)).pack()
        
        # Log
        self.log_text = tk.Text(main_frame, height=5, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
    
    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_monitoring(self):
        app_name = self.app_name.get().strip()
        if not app_name:
            messagebox.showwarning("Warning", "Please enter an application name")
            return
        
        # Add .exe if not present
        if not app_name.lower().endswith('.exe'):
            app_name += '.exe'
            self.app_name.set(app_name)
        
        # Check if app is running
        if not self.get_app_processes(app_name):
            if not messagebox.askyesno("Confirm", f"{app_name} is not currently running. Start monitoring anyway?"):
                return
        
        self.monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.app_entry.config(state=tk.DISABLED)
        self.status_text.set(f"Status: Monitoring {app_name}")
        self.log_message(f"Started monitoring {app_name}")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_application, args=(app_name,), daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.app_entry.config(state=tk.NORMAL)
        self.status_text.set("Status: Monitoring stopped")
        self.log_message("Monitoring stopped by user")
    
    def get_app_processes(self, app_name):
        matching_processes = []
        for process in psutil.process_iter(['name']):
            if process.info['name'].lower() == app_name.lower():
                matching_processes.append(process)
        return matching_processes
    
    def monitor_application(self, app_name):
        while self.monitoring:
            processes = self.get_app_processes(app_name)
            
            if not processes:
                self.log_message(f"{app_name} has been terminated. Shutting down...")
                if self.is_admin():
                    os.system("shutdown /s /t 10")
                    self.status_text.set("Status: Shutting down in 10 seconds")
                    # Update GUI before shutdown
                    self.root.update()
                    time.sleep(2)  # Give time for the message to show
                    break
                else:
                    self.log_message("Error: Insufficient privileges to shutdown")
                    self.stop_monitoring()
                    return
            
            time.sleep(2)  # Check every 2 seconds
    
    def on_closing(self):
        if self.monitoring:
            if messagebox.askokcancel("Quit", "Monitoring is active. Are you sure you want to quit?"):
                self.monitoring = False
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppMonitorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
