# Thermal Bath Controller

A GUI application for controlling and automating thermal bath temperature setpoints. This application allows setting up controlled temperature profiles with stability monitoring and logging capabilities.

## Features

- Control thermal bath temperature through serial communication
- Create multi-step temperature profiles
- Monitor temperature stability using standard deviation analysis
- Automatic logging of temperature data
- Pause/resume experiment functionality
- Configuration file management

## Installation

### Prerequisites

- Python 3.6 or higher
- Required Python packages:
  - tkinter
  - pyserial
  - numpy

### Setup

1. Clone this repository or download the source files
2. Install required packages:
   ```
   pip install pyserial numpy
   ```
3. Run the application:
   ```
   python run.py
   ```

## Usage

### Creating a Temperature Profile

1. Enter a temperature setpoint in the "Temperature Setpoint (°C)" field
2. Click "Add Setpoint" to add it to the profile
3. Repeat to add additional setpoints
4. Use "Move Up" and "Move Down" buttons to reorder steps if needed
5. Use "Remove" to delete a selected step
6. Click "Clear All" to remove all setpoints

### Setting Stability Parameters

Adjust the following parameters as needed:

- **Hold Time**: Duration to maintain temperature once stable (seconds)
- **Stability Window**: Maximum allowed standard deviation and target offset (°C)
- **Reading Interval**: Time between temperature readings (seconds)
- **Timeout**: Maximum time to wait for stability at each setpoint (seconds)
- **Min Readings**: Minimum number of readings required for stability calculation

### Running an Experiment

1. Configure serial communication settings (COM port, baudrate, etc.)
2. Enter an experiment name or use the auto-generated name
3. Click "Start" to begin the experiment
4. Use "Pause" to temporarily halt the experiment (can be resumed)
5. Use "Stop" to terminate the experiment
6. Use "Reset" to clear all settings and prepare for a new experiment

### Managing Configurations

- Click "Save Config" to save the current settings for future use
- Click "Load Config" to load a previously saved configuration

## Configuration Parameters

The application uses configuration files (*.ini) with the following sections and parameters:

### Communication Settings

```ini
[Communication]
port = COM10        # Serial port to connect to (e.g., COM10, /dev/ttyUSB0)
baudrate = 2400     # Communication baudrate
timeout = 2         # Serial read timeout in seconds
```

### Temperature Profile

```ini
[Temperature]
setpoints = 25.0, 30.0, 35.0   # Comma-separated list of temperature setpoints
```

### Stability Settings

```ini
[Stability]
hold_time = 300          # Time to maintain temperature after stability (seconds)
stability_window = 0.05  # Maximum allowed standard deviation and offset (°C)
reading_interval = 5.0   # Time between temperature readings (seconds)
timeout = 3600           # Maximum time to wait for stability (seconds)
min_readings = 10        # Minimum readings required for stability calculation
```

## Data Logging

Temperature data is logged to CSV files in the `logs` directory with the following columns:

- Timestamp
- Step number
- Target temperature
- Actual temperature
- Status

## Troubleshooting

### Common Issues

1. **Serial Connection Errors**
   - Verify the COM port is correct
   - Check physical connections
   - Ensure no other application is using the port

2. **Temperature Stability Problems**
   - Adjust the stability window parameter
   - Increase the minimum readings requirement
   - Check for external disturbances affecting the bath

3. **UI Unresponsiveness**
   - The UI will remain responsive during experiments as operations run in a background thread
   - For very long experiments, monitor the log files which are updated continuously

## Development

The application is structured as follows:

- `run.py` - Entry point for the application
- `gui.py` - Main GUI implementation
- `configs/` - Directory for configuration files
- `logs/` - Directory for temperature log files

## License

This project is licensed under the MIT License - see the LICENSE file for details.