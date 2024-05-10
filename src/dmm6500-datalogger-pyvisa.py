import pyvisa  # PyVISA library for communication with instruments over various interfaces
import csv  # CSV library for reading and writing CSV files
import time  # Time library for timestamping and time-related operations
import argparse  # Library for parsing command-line arguments

# Function to connect to the DMM (Digital Multimeter)
def connect_to_dmm(verbose=False):
    # Default resource address for the DMM
    resource_address = "USB0::0x05E6::0x6500::04453860::INSTR"
    
    try:
        # Create a resource manager instance to manage resources (instruments)
        rm = pyvisa.ResourceManager()
        
        # Try to open a connection to the instrument using the specified resource address
        inst = rm.open_resource(resource_address, timeout=500)  # Set a longer timeout for connection
        
        # Query the instrument to get its identification string
        idn = inst.query('*IDN?')
        
        if verbose:  # If verbose mode is enabled, print the command and response
            print(f"Command: *IDN?")
            print(f"Response: {idn}")
        
        # Check if the identification string contains 'DMM6500', indicating a Keithley DMM6500
        if 'DMM6500' in idn:
            print(f"Connected to Keithley DMM6500 at {resource_address}")
            return inst
        else:
            # If the instrument is not a Keithley DMM6500, close the connection
            inst.close()
            print(f"The instrument at {resource_address} is not a Keithley DMM6500.")
    except Exception as e:
        # If an exception occurs during connection attempt, print an error message
        print(f"Failed to connect to {resource_address}: {e}")

    # If connection attempt fails, print a message indicating so
    print("Failed to connect to the Keithley DMM6500.")
    return None

# Function to take a measurement from the DMM
def take_measurement(inst, measurement_type, verbose=False):
    try:
        if measurement_type == 'voltage':
            command = 'MEAS:VOLT:DC? AUTO'
        elif measurement_type == 'current':
            command = 'MEAS:CURR:DC? AUTO'
        elif measurement_type == 'resistance':
            command = 'MEAS:RES? AUTO'
        else:
            # If an invalid measurement type is provided, print an error message
            print("Invalid measurement type!")
            return None
        
        # Query the instrument with the appropriate command based on the measurement type
        measurement = inst.query(command)
        
        if verbose:  # If verbose mode is enabled, print the command and response
            print(f"Command: {command}")
            print(f"Response: {measurement}")
        
        return float(measurement)  # Convert the measurement result to a float and return
    except Exception as e:
        # If an exception occurs during measurement, print an error message
        print(f"Failed to take measurement: {e}")
        return None

# Function to record measurement data to a CSV file
def record_to_csv(data, filename):
    with open(filename, 'a', newline='') as csvfile:  # Open CSV file in append mode
        writer = csv.writer(csvfile)  # Create a CSV writer object
        writer.writerow(data)  # Write data to the CSV file

# Main entry point of the script
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Script to connect to Keithley DMM6500 and take measurements.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode')
    args = parser.parse_args()
    
    # Call the connect_to_dmm function to attempt connection to the DMM
    dmm = connect_to_dmm(args.verbose)
    if dmm:
        # Prompt the user for measurement type, CSV filename, number of samples, and sample interval
        measurement_type = input("What kind of measurement do you want to take (voltage/current/resistance)? ").lower()
        filename = input("Enter the name of the CSV file to save the measurements: ")
        num_samples = int(input("How many samples do you want to take? "))
        sample_interval = float(input("Enter the time interval between samples (in seconds): "))
        
        # Write header to CSV file
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', measurement_type.capitalize()])  # Write header row with timestamp and measurement type
        
        # Loop to take measurements and record them to the CSV file
        for _ in range(num_samples):
            measurement = take_measurement(dmm, measurement_type, args.verbose)  # Take a measurement
            if measurement is not None:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')  # Get current timestamp
                record_to_csv([timestamp, measurement], filename)  # Record timestamp and measurement to CSV file
                print(f"{timestamp} - {measurement_type.capitalize()}: {measurement}")  # Print measurement details
            time.sleep(sample_interval)  # Wait for the specified interval before taking the next measurement
