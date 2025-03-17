import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
import time
import threading
import configparser
import csv
from datetime import datetime
import serial
from typing import List, Optional
import serial.tools.list_ports

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Thermal Bath Controller")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # State variables
        self.running = False
        self.paused = False
        self.experiment_thread = None
        self.setpoints = []
        self.log_data = []
        self.serial_connection = None
        self.current_setpoint_index = 0
        
        # Create directories if they don't exist
        self.config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Get next experiment number
        self.experiment_number = self._get_next_experiment_number()
        
        # Create the UI
        self._create_ui()
        
        # Update experiment name
        self._update_experiment_name()
            
    def _create_ui(self):
            """Create the user interface."""
            # Main frame
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Top section - Experiment name and control buttons
            top_frame = ttk.Frame(main_frame)
            top_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Experiment name
            ttk.Label(top_frame, text="Experiment Name:").pack(side=tk.LEFT, padx=(0, 5))
            self.experiment_name_var = tk.StringVar()
            experiment_name_entry = ttk.Entry(top_frame, textvariable=self.experiment_name_var, width=30)
            experiment_name_entry.pack(side=tk.LEFT, padx=(0, 10))
            
            # Control buttons
            self.start_button = ttk.Button(top_frame, text="Start", command=self.start_experiment)
            self.start_button.pack(side=tk.LEFT, padx=5)
            
            self.pause_resume_button = ttk.Button(top_frame, text="Pause", command=self.toggle_pause_resume, state=tk.DISABLED)
            self.pause_resume_button.pack(side=tk.LEFT, padx=5)
            
            self.stop_button = ttk.Button(top_frame, text="Stop", command=self.stop_experiment, state=tk.DISABLED)
            self.stop_button.pack(side=tk.LEFT, padx=5)
            
            self.reset_button = ttk.Button(top_frame, text="Reset", command=self.reset_experiment)
            self.reset_button.pack(side=tk.LEFT, padx=5)
            
            self.load_config_button = ttk.Button(top_frame, text="Load Config", command=self.load_config_file)
            self.load_config_button.pack(side=tk.LEFT, padx=5)
            
            # Middle section - Two columns
            middle_frame = ttk.Frame(main_frame)
            middle_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Left column - Settings
            left_frame = ttk.LabelFrame(middle_frame, text="Settings", padding="10")
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            # Serial settings
            serial_frame = ttk.Frame(left_frame)
            serial_frame.pack(fill=tk.X, pady=5)
            ttk.Label(serial_frame, text="COM Port:").grid(row=0, column=0, sticky=tk.W, padx=5)
            self.port_var = tk.StringVar(value="COM10")
            ttk.Entry(serial_frame, textvariable=self.port_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)

            # Add scan button
            scan_button = ttk.Button(serial_frame, text="Scan", command=self.scan_com_ports)
            scan_button.grid(row=0, column=2, sticky=tk.W, padx=5)

            ttk.Label(serial_frame, text="Baudrate:").grid(row=0, column=3, sticky=tk.W, padx=5)
            self.baudrate_var = tk.IntVar(value=2400)
            ttk.Entry(serial_frame, textvariable=self.baudrate_var, width=10).grid(row=0, column=4, sticky=tk.W, padx=5)
            
            ttk.Label(serial_frame, text="Timeout:").grid(row=1, column=0, sticky=tk.W, padx=5)
            self.timeout_var = tk.IntVar(value=2)
            ttk.Entry(serial_frame, textvariable=self.timeout_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5)
            
            # Set temperature frame
            temp_frame = ttk.Frame(left_frame)
            temp_frame.pack(fill=tk.X, pady=5)
            ttk.Label(temp_frame, text="Temperature Setpoint (°C):").pack(side=tk.LEFT, padx=5)
            self.setpoint_var = tk.DoubleVar(value=25.0)
            ttk.Entry(temp_frame, textvariable=self.setpoint_var, width=10).pack(side=tk.LEFT, padx=5)
            ttk.Button(temp_frame, text="Add Setpoint", command=self.add_setpoint).pack(side=tk.LEFT, padx=5)
            
            # Stability settings
            stability_frame = ttk.LabelFrame(left_frame, text="Stability Settings", padding="5")
            stability_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(stability_frame, text="Hold Time (s):").grid(row=0, column=0, sticky=tk.W, padx=5)
            self.hold_time_var = tk.IntVar(value=300)
            ttk.Entry(stability_frame, textvariable=self.hold_time_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
            
            ttk.Label(stability_frame, text="Stability Window (°C):").grid(row=0, column=2, sticky=tk.W, padx=5)
            self.stability_window_var = tk.DoubleVar(value=0.05)
            ttk.Entry(stability_frame, textvariable=self.stability_window_var, width=10).grid(row=0, column=3, sticky=tk.W, padx=5)
            
            ttk.Label(stability_frame, text="Reading Interval (s):").grid(row=1, column=0, sticky=tk.W, padx=5)
            self.reading_interval_var = tk.DoubleVar(value=5.0)
            ttk.Entry(stability_frame, textvariable=self.reading_interval_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5)
            
            ttk.Label(stability_frame, text="Timeout (s):").grid(row=1, column=2, sticky=tk.W, padx=5)
            self.timeout_duration_var = tk.IntVar(value=3600)
            ttk.Entry(stability_frame, textvariable=self.timeout_duration_var, width=10).grid(row=1, column=3, sticky=tk.W, padx=5)
            
            ttk.Label(stability_frame, text="Min Readings:").grid(row=2, column=0, sticky=tk.W, padx=5)
            self.min_readings_var = tk.IntVar(value=10)
            ttk.Entry(stability_frame, textvariable=self.min_readings_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5)
            # Right column - Setpoints and Status
            right_frame = ttk.Frame(middle_frame)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
            
            # Setpoints list - Using a treeview for better visualization
            setpoints_frame = ttk.LabelFrame(right_frame, text="Temperature Steps", padding="10")
            setpoints_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            
            # Create treeview for steps
            self.setpoints_tree = ttk.Treeview(setpoints_frame, columns=('step', 'temp'), show='headings')
            self.setpoints_tree.heading('step', text='Step')
            self.setpoints_tree.heading('temp', text='Temperature (°C)')
            self.setpoints_tree.column('step', width=50)
            self.setpoints_tree.column('temp', width=150)
            
            # Scrollbar for treeview
            setpoints_scrollbar = ttk.Scrollbar(setpoints_frame, orient=tk.VERTICAL, command=self.setpoints_tree.yview)
            self.setpoints_tree.configure(yscrollcommand=setpoints_scrollbar.set)
            
            # Pack treeview and scrollbar
            self.setpoints_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            setpoints_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Setpoint buttons for managing steps
            setpoint_buttons_frame = ttk.Frame(setpoints_frame)
            setpoint_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)  # Change to pack on right with Y fill

            # Create a uniform grid for the buttons
            setpoint_buttons_frame.columnconfigure(0, weight=1)
            setpoint_buttons_frame.columnconfigure(1, weight=1)
            setpoint_buttons_frame.columnconfigure(2, weight=1)
            setpoint_buttons_frame.columnconfigure(3, weight=1)

            # Add buttons in a vertical layout
            move_up_btn = ttk.Button(setpoint_buttons_frame, text="Move Up", command=self._move_step_up)
            move_up_btn.pack(fill=tk.X, pady=2)  # Use pack instead of grid, with X fill and Y padding

            move_down_btn = ttk.Button(setpoint_buttons_frame, text="Move Down", command=self._move_step_down)
            move_down_btn.pack(fill=tk.X, pady=2)

            remove_btn = ttk.Button(setpoint_buttons_frame, text="Remove", command=self.remove_selected_setpoint)
            remove_btn.pack(fill=tk.X, pady=2)

            clear_btn = ttk.Button(setpoint_buttons_frame, text="Clear All", command=self.clear_setpoints)
            clear_btn.pack(fill=tk.X, pady=2)
            
            # Bottom section - Log and status
            bottom_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
            bottom_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Status text
            status_scrollbar = ttk.Scrollbar(bottom_frame)
            status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.status_text = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, height=10)
            self.status_text.pack(fill=tk.BOTH, expand=True)
            self.status_text.config(state=tk.DISABLED)
            
            # Current temperature display
            status_bar = ttk.Frame(main_frame)
            status_bar.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Label(status_bar, text="Current Temperature:").pack(side=tk.LEFT, padx=(0, 5))
            self.current_temp_var = tk.StringVar(value="--")
            ttk.Label(status_bar, textvariable=self.current_temp_var, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
            
            # Current step display
            ttk.Label(status_bar, text="   Current Step:").pack(side=tk.LEFT, padx=(10, 5))
            self.current_step_var = tk.StringVar(value="--")
            ttk.Label(status_bar, textvariable=self.current_step_var, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
    def _get_next_experiment_number(self) -> int:
        """Get the next experiment number by checking existing config files."""
        experiment_numbers = []
        if os.path.exists(self.config_dir):
            for filename in os.listdir(self.config_dir):
                if filename.startswith("experiment_") and filename.endswith(".ini"):
                    try:
                        num = int(filename.split("_")[1].split(".")[0])
                        experiment_numbers.append(num)
                    except (IndexError, ValueError):
                        continue
        
        if not experiment_numbers:
            return 1
        return max(experiment_numbers) + 1
    
    def _update_experiment_name(self):
        """Update the experiment name field with the default name."""
        self.experiment_name_var.set(f"experiment_{self.experiment_number}")
    
    def log_message(self, message: str):
        """Add a message to the log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, full_message)
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # Also print to console
        print(full_message.strip())
    
    def add_setpoint(self):
        """Add a temperature setpoint to the list."""
        try:
            setpoint = self.setpoint_var.get()
            if setpoint not in self.setpoints:
                self.setpoints.append(setpoint)
                self._update_setpoints_tree()
                self.log_message(f"Added setpoint: {setpoint}°C")
            else:
                messagebox.showinfo("Duplicate", f"Setpoint {setpoint}°C already exists.")
        except tk.TclError:
            messagebox.showerror("Invalid Input", "Please enter a valid temperature.")
    
    def remove_selected_setpoint(self):
        """Remove the selected setpoint from the list."""
        selected = self.setpoints_tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a setpoint to remove.")
            return
            
        # Get the first selected item
        item_id = selected[0]
        item_values = self.setpoints_tree.item(item_id, 'values')
        
        # Convert step number to index (step numbers start from 1)
        try:
            step_index = int(item_values[0]) - 1
            
            # Ensure index is valid
            if 0 <= step_index < len(self.setpoints):
                # Get the setpoint value before removing it
                setpoint = self.setpoints[step_index]
                
                # Remove the setpoint from the list
                self.setpoints.pop(step_index)
                
                # Update the treeview
                self._update_setpoints_tree()
                
                # Log the removal
                self.log_message(f"Removed setpoint: {setpoint}°C")
            else:
                self.log_message("Error: Invalid step index")
        except (ValueError, IndexError) as e:
            self.log_message(f"Error removing setpoint: {str(e)}")
        self._update_setpoints_tree()
    
    def clear_setpoints(self):
        """Clear all setpoints from the list."""
        self.setpoints = []
        self._update_setpoints_tree()
        self.log_message("Cleared all setpoints")
    
    def _move_step_up(self):
        """Move the selected step up in the sequence."""
        selected = self.setpoints_tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a step to move.")
            return
            
        item_id = selected[0]  # Get the first selected item
        item_values = self.setpoints_tree.item(item_id, 'values')
        step_index = int(item_values[0]) - 1
        
        if step_index > 0:
            # Swap with previous item
            self.setpoints[step_index], self.setpoints[step_index-1] = self.setpoints[step_index-1], self.setpoints[step_index]
            self._update_setpoints_tree()
            
            # Select the moved item
            new_item_id = self.setpoints_tree.get_children()[step_index-1]
            self.setpoints_tree.selection_set(new_item_id)
            self.setpoints_tree.see(new_item_id)
    
    def _move_step_down(self):
        """Move the selected step down in the sequence."""
        selected = self.setpoints_tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a step to move.")
            return
            
        item_id = selected[0]  # Get the first selected item
        item_values = self.setpoints_tree.item(item_id, 'values')
        step_index = int(item_values[0]) - 1
        
        if step_index < len(self.setpoints) - 1:
            # Swap with next item
            self.setpoints[step_index], self.setpoints[step_index+1] = self.setpoints[step_index+1], self.setpoints[step_index]
            self._update_setpoints_tree()
            
            # Select the moved item
            new_item_id = self.setpoints_tree.get_children()[step_index+1]
            self.setpoints_tree.selection_set(new_item_id)
            self.setpoints_tree.see(new_item_id)
    
    def _update_setpoints_tree(self):
        """Update the setpoints treeview with current values."""
        # Clear existing items
        for item in self.setpoints_tree.get_children():
            self.setpoints_tree.delete(item)
            
        # Add setpoints as steps
        for i, setpoint in enumerate(self.setpoints):
            self.setpoints_tree.insert('', 'end', values=(i+1, f"{setpoint:.2f}"))
    
    def create_config_file(self) -> str:
        """Create a configuration file for the current experiment settings."""
        config = configparser.ConfigParser()
        
        # Communication settings
        config["Communication"] = {
            "port": self.port_var.get(),
            "baudrate": str(self.baudrate_var.get()),
            "timeout": str(self.timeout_var.get())
        }
        
        # Temperature setpoints
        config["Temperature"] = {
            "setpoints": ", ".join(str(temp) for temp in self.setpoints)
        }
        
        # Stability settings
        config["Stability"] = {
            "hold_time": str(self.hold_time_var.get()),
            "stability_window": str(self.stability_window_var.get()),
            "reading_interval": str(self.reading_interval_var.get()),
            "timeout": str(self.timeout_duration_var.get()),
            "min_readings": str(self.min_readings_var.get())
        }
        
        # Save to file
        experiment_name = self.experiment_name_var.get()
        if not experiment_name:
            experiment_name = f"experiment_{self.experiment_number}"
            self.experiment_name_var.set(experiment_name)
            
        config_path = os.path.join(self.config_dir, f"{experiment_name}.ini")
        
        with open(config_path, 'w') as configfile:
            config.write(configfile)
            
        self.log_message(f"Created config file: {config_path}")
        return config_path
    
    def save_log_data(self):
        """Save the temperature log data to a CSV file."""
        if not self.log_data:
            return
            
        experiment_name = self.experiment_name_var.get()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(self.log_dir, f"{experiment_name}_{timestamp}.csv")
        
        with open(log_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp", "Step", "Target Temperature", "Actual Temperature", "Status"])
            writer.writerows(self.log_data)
            
        self.log_message(f"Saved log data to: {log_path}")
    
    def toggle_pause_resume(self):
        """Toggle between pause and resume states."""
        if not self.running:
            return
        
        if self.paused:
            # Resume experiment
            self.paused = False
            self.pause_resume_button.config(text="Pause")
            self.log_message("Experiment resumed")
        else:
            # Pause experiment
            self.paused = True
            self.pause_resume_button.config(text="Resume")
            self.log_message("Experiment paused")
    
    def start_experiment(self):
        """Start the experiment with current settings."""
        if self.running:
            return
            
        # Check if there are any setpoints
        if not self.setpoints:
            messagebox.showerror("No Setpoints", "Please add at least one temperature setpoint.")
            return
            
        # Create config file
        config_path = self.create_config_file()
        
        # Start experiment in a new thread
        self.running = True
        self.paused = False
        self.current_setpoint_index = 0
        self.start_button.config(state=tk.DISABLED)
        self.pause_resume_button.config(state=tk.NORMAL, text="Pause")
        self.stop_button.config(state=tk.NORMAL)  # Enable the stop button
        
        self.experiment_thread = threading.Thread(target=self._run_experiment, daemon=True)
        self.experiment_thread.start()
        
        self.log_message("Experiment started")
    
    def reset_experiment(self):
        """Reset the experiment settings."""
        if self.running:
            messagebox.showinfo("Experiment Running", "Please stop the experiment before resetting.")
            return
            
        # Save log data if any exists
        if self.log_data:
            self.save_log_data()
            
        # Increment experiment number and reset settings
        self.experiment_number = self._get_next_experiment_number()
        self._update_experiment_name()
        
        self.setpoints = []
        self._update_setpoints_tree()
        self.log_data = []
        self.current_setpoint_index = 0
        
        # Reset status display
        self.current_temp_var.set("--")
        self.current_step_var.set("--")
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # Enable start button and disable others
        self.start_button.config(state=tk.NORMAL)
        self.pause_resume_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)  # Ensure stop button is disabled
        
        self.log_message("Experiment reset")
    
    def _run_experiment(self):
        """Run the experiment in a separate thread."""
        try:
            # Initialize the serial connection
            try:
                self.log_message(f"Connecting to port {self.port_var.get()}...")
                self.serial_connection = serial.Serial(
                    port=self.port_var.get(),
                    baudrate=self.baudrate_var.get(),
                    bytesize=serial.EIGHTBITS,
                    stopbits=serial.STOPBITS_ONE,
                    parity=serial.PARITY_NONE,
                    timeout=self.timeout_var.get(),
                    rtscts=True,
                    xonxoff=False,
                    dsrdtr=False
                )
                self.log_message("Serial connection established")
            except Exception as e:
                self.log_message(f"Error connecting to serial port: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Connection Error", 
                                                                f"Could not connect to port {self.port_var.get()}: {str(e)}"))
                self.root.after(0, self._experiment_completed)
                return
            
            # Get stability parameters
            hold_time = self.hold_time_var.get()
            stability_window = self.stability_window_var.get()
            reading_interval = self.reading_interval_var.get()
            timeout_duration = self.timeout_duration_var.get()
            min_readings = self.min_readings_var.get()
            
            # Read initial temperature
            current_temp = self._read_temperature()
            if current_temp is not None:
                self.log_message(f"Initial temperature: {current_temp}°C")
                self.root.after(0, lambda t=current_temp: self.current_temp_var.set(f"{t:.2f}°C"))
            
            # Process each setpoint
            while self.current_setpoint_index < len(self.setpoints) and self.running:
                setpoint = self.setpoints[self.current_setpoint_index]
                step_number = self.current_setpoint_index + 1
                
                # Update current step indicator
                self.root.after(0, lambda s=step_number, t=setpoint: 
                              self.current_step_var.set(f"Step {s}: {t:.2f}°C"))
                
                # Handle pause state
                while self.paused and self.running:
                    time.sleep(0.5)
                
                # If we're no longer running (stopped during pause), exit
                if not self.running:
                    break
                    
                self.log_message(f"Step {step_number}: Setting temperature to {setpoint}°C")
                self._set_temperature(setpoint)
                
                # Initialize tracking variables
                start_time = time.time()
                stability_start_time = None
                temperature_readings = []
                
                # Wait for temperature to stabilize
                while self.running:
                    # Handle pause state
                    while self.paused and self.running:
                        time.sleep(0.5)
                    
                    # If we're no longer running (stopped during pause), exit
                    if not self.running:
                        break
                        
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    
                    if elapsed_time > timeout_duration:
                        self.log_message(f"Timeout reached while waiting for stability at {setpoint}°C")
                        break
                        
                    # Read current temperature
                    temp = self._read_temperature()
                    if temp is not None:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        status = "Waiting for stability"
                        self.log_data.append([timestamp, step_number, setpoint, temp, status])
                        temperature_readings.append(temp)
                        self.root.after(0, lambda t=temp: self.current_temp_var.set(f"{t:.2f}°C"))
                        
                    # Check if temperature is stable
                    is_stable = self._is_temperature_stable(temperature_readings, 
                                                           setpoint, 
                                                           stability_window, 
                                                           min_readings)
                                                           
                    if is_stable:
                        if stability_start_time is None:
                            stability_start_time = current_time
                            self.log_message(f"Temperature stable at {setpoint}°C, holding for {hold_time} seconds")
                        
                        # Update status in log data
                        remaining = hold_time - (current_time - stability_start_time)
                        if remaining > 0:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            status = f"Stable - Holding ({int(remaining)}s remaining)"
                            if temp is not None:
                                self.log_data.append([timestamp, step_number, setpoint, temp, status])
                        
                        # Check if we've held the temperature long enough
                        if current_time - stability_start_time >= hold_time:
                            self.log_message(f"Completed hold time for {setpoint}°C")
                            break
                    else:
                        # Reset stability timer if temperature becomes unstable
                        stability_start_time = None
                        
                    time.sleep(reading_interval)
                
                # If we're no longer running, exit the loop
                if not self.running:
                    break
                    
                # Move to next setpoint
                self.current_setpoint_index += 1
            
            if self.current_setpoint_index >= len(self.setpoints):
                self.log_message("All steps completed!")
            else:
                self.log_message("Experiment stopped before completion")
            
        except Exception as e:
            self.log_message(f"Error during experiment: {str(e)}")
        finally:
            # Close the serial connection
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.log_message("Serial connection closed")
                
            # Save the log data
            self.save_log_data()
                
            # Reset the UI
            self.root.after(0, self._experiment_completed)
    
    def _experiment_completed(self):
        """Update UI after experiment completion."""
        self.running = False
        self.paused = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_resume_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)  # Disable the stop button
        self.current_step_var.set("--")
    
    def _read_temperature(self) -> Optional[float]:
        """Read the current temperature from the bath."""
        try:
            self.serial_connection.write(b"t\r")
            time.sleep(0.5)
            response = self.serial_connection.read_until().decode('latin-1').strip()
            
            try:
                # Try to extract the temperature value from the response
                temp = float(response.split(" ")[-2])
                return temp
            except ValueError:
                self.log_message(f"Could not parse temperature: {response}")
                return None
                
        except Exception as e:
            self.log_message(f"Error reading temperature: {str(e)}")
            return None
    
    def _set_temperature(self, temperature: float) -> bool:
        """Set the bath temperature setpoint."""
        try:
            command = f"s={temperature}\r"
            self.serial_connection.write(command.encode())
            time.sleep(0.5)
            response = self.serial_connection.read_until().decode('latin-1').strip()
            return True
        except Exception as e:
            self.log_message(f"Error setting temperature: {str(e)}")
            return False
    
    def _is_temperature_stable(self, temperatures: List[float], 
                              target: float, 
                              stability_window: float = 0.05, 
                              min_readings: int = 10) -> bool:
        """Check if temperature is stable."""
        if len(temperatures) < min_readings:
            return False
            
        # Use the last min_readings temperatures
        recent = temperatures[-min_readings:]
        
        # Calculate moving average and standard deviation
        avg = sum(recent) / len(recent)
        std = (sum((x - avg) ** 2 for x in recent) / len(recent)) ** 0.5
        
        # Check if temperature is close to target and stable
        is_stable = (std <= stability_window) and (abs(avg - target) <= stability_window)
        
        status = f"Current: {recent[-1]:.3f}, Avg: {avg:.3f}, Std: {std:.3f}, Stable: {is_stable}"
        self.log_message(status)
        
        return is_stable

    def load_config_file(self):
        """Open a file dialog to load an existing configuration file."""
        if self.running:
            messagebox.showinfo("Experiment Running", "Please stop the current experiment before loading a config file.")
            return
            
        # Ask user to select a config file
        config_file = filedialog.askopenfilename(
            title="Select Configuration File",
            initialdir=self.config_dir,
            filetypes=[("Configuration Files", "*.ini"), ("All Files", "*.*")]
        )
        
        if not config_file:  # User cancelled
            return
            
        try:
            # Load the configuration
            config = configparser.ConfigParser()
            config.read(config_file)
            
            # Extract the experiment name from file path
            filename = os.path.basename(config_file)
            experiment_name = os.path.splitext(filename)[0]
            self.experiment_name_var.set(experiment_name)
            
            # Load communication settings
            if 'Communication' in config:
                self.port_var.set(config['Communication'].get('port', 'COM10'))
                self.baudrate_var.set(config['Communication'].getint('baudrate', 2400))
                self.timeout_var.set(config['Communication'].getint('timeout', 2))
            
            # Load temperature setpoints
            self.setpoints = []
            if 'Temperature' in config:
                setpoints_str = config['Temperature'].get('setpoints', '')
                if setpoints_str:
                    try:
                        self.setpoints = [float(x.strip()) for x in setpoints_str.split(',')]
                        self._update_setpoints_tree()
                    except ValueError:
                        messagebox.showerror("Error", "Failed to parse setpoints from config file.")
            
            # Load stability settings
            if 'Stability' in config:
                self.hold_time_var.set(config['Stability'].getint('hold_time', 300))
                self.stability_window_var.set(config['Stability'].getfloat('stability_window', 0.05))
                self.reading_interval_var.set(config['Stability'].getfloat('reading_interval', 5.0))
                self.timeout_duration_var.set(config['Stability'].getint('timeout', 3600))
                self.min_readings_var.set(config['Stability'].getint('min_readings', 10))
            
            self.log_message(f"Loaded configuration from: {config_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")

    def stop_experiment(self):
        """Stop the experiment completely (not just pause)."""
        if not self.running:
            return
            
        if messagebox.askyesno("Stop Experiment", "Are you sure you want to stop the experiment? This will end the current experiment."):
            self.running = False
            self.log_message("Experiment stopping...")
            
            # Disable pause/resume button immediately
            self.pause_resume_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)

    def scan_com_ports(self):
        """Scan for available COM ports and update the port selection."""
        try:
            # Clear current selection
            self.port_var.set("")
            
            # Get list of available ports
            ports = list(serial.tools.list_ports.comports())
            
            if not ports:
                self.log_message("No COM ports detected.")
                messagebox.showinfo("Port Scan", "No COM ports were detected on this system.")
                self.port_var.set("COM10")  # Set default value
                return
                
            # Create a port selection window
            port_window = tk.Toplevel(self.root)
            port_window.title("Select COM Port")
            port_window.geometry("400x300")
            port_window.minsize(400, 300)
            port_window.resizable(True, True)
            port_window.transient(self.root)
            port_window.grab_set()
            
            # Add description label
            ttk.Label(port_window, text="Available COM Ports:", 
                     font=("Arial", 12, "bold")).pack(pady=10)
            
            # Create a frame for the listbox and scrollbar
            list_frame = ttk.Frame(port_window)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Create listbox with scrollbar
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            port_listbox = tk.Listbox(list_frame, font=("Courier New", 10), 
                                     yscrollcommand=scrollbar.set)
            port_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar.config(command=port_listbox.yview)
            
            # Populate listbox with ports
            for i, port in enumerate(ports):
                port_name = port.device
                description = f"{port_name} - {port.description}"
                port_listbox.insert(tk.END, description)
                
                # If this port contains "USB" or "Serial", preselect it
                if "USB" in port.description or "Serial" in port.description:
                    port_listbox.selection_set(i)
            
            # Function to handle port selection
            def select_port():
                selection = port_listbox.curselection()
                if selection:
                    selected_port = ports[selection[0]].device
                    self.port_var.set(selected_port)
                    self.log_message(f"Selected port: {selected_port}")
                else:
                    self.log_message("No port selected.")
                port_window.destroy()
            
            # Add buttons
            button_frame = ttk.Frame(port_window)
            button_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(button_frame, text="Select", command=select_port).pack(side=tk.RIGHT, padx=10)
            ttk.Button(button_frame, text="Cancel", command=port_window.destroy).pack(side=tk.RIGHT, padx=10)
            
            # Log the scan
            self.log_message(f"Found {len(ports)} COM ports")
            
            # Center the window on parent
            port_window.update_idletasks()
            width = port_window.winfo_width()
            height = port_window.winfo_height()
            x = self.root.winfo_x() + (self.root.winfo_width() - width) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - height) // 2
            port_window.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            self.log_message(f"Error scanning COM ports: {str(e)}")
            messagebox.showerror("Error", f"Failed to scan COM ports: {str(e)}")

# Main entry point
def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()