# Multimeter Data Logger

This Python script connects to a Keithley DMM6500 multimeter via USB and records measurements in a CSV file. It prompts the user to specify the measurement mode (e.g., voltage, current, resistance) and the name of the CSV file where the data will be stored.

## Prerequisites

- Python 3.x
- PyVISA library (`pip install pyvisa`)

## Setup

1. Connect the Keithley DMM6500 multimeter to your computer via USB.
2. Install the PyVISA library if you haven't already (`pip install pyvisa`).

## How to Run

1. Clone or download the repository.
2. Open a terminal or command prompt and navigate to the directory containing the script.
3. Run the script using Python:

   ```
   python multimeter_logger.py
   ```

4. Follow the on-screen prompts to enter the measurement mode and CSV file name.
5. The script will start recording measurements from the multimeter and save them to the specified CSV file.
6. Press `Ctrl + C` to stop the script at any time.

## Notes

- Ensure that the correct USB address of the multimeter is provided in the script (`USB0::0x05E6::0x6500::04453860::INSTR`).
- The default measurement range is set to a large value (`100000`), which may need adjustment based on the expected range of measurements.
- The script records a specified number of measurements at a specified interval.
- Any errors encountered during execution will be displayed on the console.

