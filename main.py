import serial
import time
import string
import numpy as np
import configparser
import os
from typing import List, Union, Optional

def load_config(config_file="config.ini"):
    """Load configuration from file."""
    config = configparser.ConfigParser()
    
    # Check if config file exists
    if not os.path.exists(config_file):
        print(f"Config file {config_file} not found. Using default settings.")
        return None
    
    config.read(config_file)
    return config

def initialize_serial(port="COM1", baudrate=2400, timeout=2):
    """Initialize the serial connection to the Fluke 7320 bath."""
    ser = serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
        parity=serial.PARITY_NONE,
        timeout=timeout,
        rtscts=True,   # Disable RTS/CTS flow control
        xonxoff=False,  # Disable XON/XOFF flow control
        dsrdtr=False    # Disable DSR/DTR flow control
    )
    return ser

def send_command(ser, command):
    """Send a command and read the response."""
    ser.write(f"{command}\r".encode())  # Ensure carriage return '\r'
    time.sleep(0.5)  # Allow time for response
    response = ser.read_until().decode('latin-1').strip()  # Use 'latin-1' decoding
    print(f"Response: {response}")  # Debugging output
    return response

def set_temperature(ser, temp):
    """Set the temperature setpoint."""
    command = f"s={temp}"
    response = send_command(ser, command)
    return response
    
def read_temperature(ser) -> float:
    """Read the current bath temperature and return as float."""
    command = "t"
    response = send_command(ser, command)
    try:
        # Extract numeric value from response
        temp = float(response)
        return temp
    except ValueError:
        print(f"Could not convert temperature response to float: {response}")
        return None

def command(ser, command):
    response = send_command(ser, command)
    return response

def is_temperature_stable(temperatures: List[float], 
                          target: float, 
                          stability_window: float = 0.05, 
                          min_readings: int = 10) -> bool:
    """
    Check if temperature is stable by analyzing recent readings.
    
    Args:
        temperatures: List of recent temperature readings
        target: Target temperature
        stability_window: Maximum allowed standard deviation
        min_readings: Minimum number of readings needed for stability check
        
    Returns:
        bool: True if temperature is stable
    """
    if len(temperatures) < min_readings:
        return False
        
    # Use the last min_readings temperatures
    recent = temperatures[-min_readings:]
    
    # Calculate moving average and standard deviation
    avg = np.mean(recent)
    std = np.std(recent)
    
    # Check if temperature is close to target and stable
    is_stable = (std <= stability_window) and (abs(avg - target) <= stability_window)
    
    print(f"Current: {recent[-1]:.3f}, Avg: {avg:.3f}, Std: {std:.3f}, Stable: {is_stable}")
    return is_stable

def maintain_temperature_setpoints(ser, 
                                  setpoints: List[float], 
                                  hold_time: int = 300,
                                  stability_window: float = 0.05,
                                  reading_interval: float = 5.0,
                                  timeout: int = 3600,
                                  min_readings: int = 10):
    """
    Maintain each temperature setpoint for the specified time after stability is reached.
    
    Args:
        ser: Serial connection
        setpoints: List of temperature setpoints
        hold_time: Time to maintain each setpoint after stability (seconds)
        stability_window: Maximum allowed standard deviation for stability
        reading_interval: Time between temperature readings (seconds)
        timeout: Maximum time to wait for stability at each setpoint (seconds)
        min_readings: Minimum number of readings for stability check
    """
    for setpoint in setpoints:
        print(f"\nSetting temperature to {setpoint}°C")
        set_temperature(ser, setpoint)
        
        # Initialize tracking variables
        start_time = time.time()
        stability_start_time = None
        temperature_readings = []
        
        # Wait for temperature to stabilize
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            if elapsed_time > timeout:
                print(f"Timeout reached while waiting for stability at {setpoint}°C")
                break
                
            # Read current temperature
            temp = read_temperature(ser)
            if temp is not None:
                temperature_readings.append(temp)
                
            # Check if temperature is stable
            if is_temperature_stable(temperature_readings, setpoint, stability_window, min_readings):
                if stability_start_time is None:
                    stability_start_time = current_time
                    print(f"Temperature stable at {setpoint}°C, holding for {hold_time} seconds")
                
                # Check if we've held the temperature long enough
                if current_time - stability_start_time >= hold_time:
                    print(f"Completed hold time for {setpoint}°C")
                    break
            else:
                # Reset stability timer if temperature becomes unstable
                stability_start_time = None
                
            time.sleep(reading_interval)

def main():
    """Main function to set up calibration and automate the process."""
    # Load configuration
    config = load_config()
    
    # Get communication settings
    port = "COM10"  # Default
    baudrate = 2400
    timeout = 2
    
    if config and 'Communication' in config:
        port = config['Communication'].get('port', port)
        baudrate = config['Communication'].getint('baudrate', baudrate)
        timeout = config['Communication'].getint('timeout', timeout)
    
    # Initialize serial connection
    ser = initialize_serial(port=port, baudrate=baudrate, timeout=timeout)
    
    # Get temperature setpoints
    setpoints = [25.0, 30.0, 35.0]  # Default
    
    if config and 'Temperature' in config:
        # Parse comma-separated list of floats
        setpoints_str = config['Temperature'].get('setpoints', '')
        if setpoints_str:
            try:
                setpoints = [float(x.strip()) for x in setpoints_str.split(',')]
                print(f"Loaded setpoints from config: {setpoints}")
            except ValueError:
                print(f"Error parsing setpoints from config. Using defaults: {setpoints}")
    
    # Get stability settings
    hold_time = 300
    stability_window = 0.05
    reading_interval = 5.0
    timeout_duration = 3600
    min_readings = 10
    
    if config and 'Stability' in config:
        hold_time = config['Stability'].getint('hold_time', hold_time)
        stability_window = config['Stability'].getfloat('stability_window', stability_window)
        reading_interval = config['Stability'].getfloat('reading_interval', reading_interval)
        timeout_duration = config['Stability'].getint('timeout', timeout_duration)
        min_readings = config['Stability'].getint('min_readings', min_readings)
    
    try:
        # Check initial temperature
        current_temp = read_temperature(ser)
        print(f"Initial temperature: {current_temp}°C")
        
        # Run through temperature setpoints
        maintain_temperature_setpoints(
            ser, 
            setpoints, 
            hold_time=hold_time,
            stability_window=stability_window,
            reading_interval=reading_interval,
            timeout=timeout_duration,
            min_readings=min_readings
        )
    
    finally:
        ser.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()