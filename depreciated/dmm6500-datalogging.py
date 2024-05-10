import csv
import time
from DMM6500 import DMM6500  # Importing DMM6500 class directly from DMM6500 module in the same directory

# Prompt user for measurement mode
measurement_mode = input("Enter measurement mode (e.g., voltage, current, resistance): ")

# Prompt user for CSV file name
csv_file = input("Enter CSV file name (without extension): ")  # Wait for user input for file name
csv_file += ".csv"  # Add the file extension

try:
    # Set up connection to the instrument over USB
    dmm = DMM6500("USB0::0x05E6::0x6500::4453860::INSTR")

    # Print some debugging information to verify the connection
    print("Connected to the instrument:", dmm)

    # Check if the measure_units() method is implemented correctly
    measurement_units = dmm.measure_units(measurement_mode)
    print("Measurement units:", measurement_units)

    # Set up CSV file for data recording
    csv_header = ['Timestamp', f'{measurement_mode.capitalize()} ({measurement_units})']
    with open(csv_file, 'w', newline='') as file:  # Open the CSV file in write mode
        writer = csv.writer(file)  # Create CSV writer object
        writer.writerow(csv_header)  # Write the header row to the CSV file

    # Set up measurement parameters
    measurement_count = 10  # Number of measurements to record
    measurement_interval = 1  # Interval between measurements in seconds

    # Perform measurements and record data
    for i in range(measurement_count):  # Loop for the specified number of measurements
        measurement = dmm.measure(measurement_mode)  # Measure data in the specified mode
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')  # Get current timestamp
        data_row = [timestamp, measurement]  # Create a list containing timestamp and measurement value

        # Append data to CSV file
        with open(csv_file, 'a', newline='') as file:  # Open the CSV file in append mode
            writer = csv.writer(file)  # Create CSV writer object
            writer.writerow(data_row)  # Write the data row to the CSV file

        # Print the measurement along with the measurement unit
        print(f"Measurement {i + 1}/{measurement_count}: {timestamp}: {measurement} {measurement_units}")

        time.sleep(measurement_interval)  # Wait for the specified interval between measurements

    # Close the connection
    dmm.close()  # Close the connection to the DMM

except Exception as e:
    print(f"An error occurred: {e}")
