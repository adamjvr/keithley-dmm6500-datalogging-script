# Import necessary libraries and modules
import pyvisa  # Import PyVISA library for communication with instruments
import csv  # Import CSV module for reading and writing CSV files
import time  # Import time module for time-related functions
from tqdm import tqdm  # Import tqdm for displaying progress bars
import re  # Import re module for regular expressions
from enum import Enum  # Import Enum class for creating enumeration types
from typing import Union, Callable  # Import Union and Callable for type hints

# Define a dummy class for visa.Resource for testing purposes
class DummyVisaResource:
    @staticmethod
    def write(txt):
        print(f'scpi write: {txt}')  # Print the SCPI command sent for debugging purposes

    @staticmethod
    def query(txt):
        print(f'scpi query: {txt}')  # Print the SCPI query sent for debugging purposes
        return ""  # Return an empty string as a dummy response

# Union type for specifying multiple types for the instrument resource
MMResourceType = Union[pyvisa.resources.Resource, DummyVisaResource]

# Define SCPI commands and their parameters using Enum
class Function(Enum):
    DC_VOLTAGE = 'VOLT:DC'
    AC_VOLTAGE = 'VOLT:AC'
    DC_CURRENT = 'CURR:DC'
    AC_CURRENT = 'CURR:AC'
    RESISTANCE = 'RES'
    FOUR_WIRE_RESISTANCE = 'FRES'
    DIODE = 'DIO'
    CAPACITANCE = 'CAP'
    TEMPERATURE = 'TEMP'
    CONTINUITY = 'CON'
    FREQUENCY = 'FREQ'
    PERIOD = 'PER'
    VOLTAGE_RATIO = 'VOLT:RAT'

    def __str__(self):
        return self.value

# Define SCPI screen commands using Enum
class Screen(Enum):
    HOME = 'HOME'
    HOME_LARGE = 'HOME_LARGE_READING'
    READING_TABLE = 'READING_TABLE'
    GRAPH = 'GRAPH'
    HISTOGRAM = 'HISTOGRAM'
    SWIPE_FUNCTIONS = 'SWIPE_FUNCTIONS'
    SWIPE_GRAPH = 'SWIPE_GRAPH'
    SWIPE_SECONDARY = 'SWIPE_SECONDARY'
    SWIPE_SETTINGS = 'SWIPE_SETTINGS'
    SWIPE_STATISTICS = 'SWIPE_STATISTICS'
    SWIPE_USER = 'SWIPE_USER'
    SWIPE_CHANNEL = 'SWIPE_CHANNEL'
    SWIPE_NONSWITCH = 'SWIPE_NONSWITCH'
    SWIPE_SCAN = 'SWIPE_SCAN'
    CHANNEL_CONTROL = 'CHANNEL_CONTROL'
    CHANNEL_SETTINGS = 'CHANNEL_SETTINGS'
    CHANNEL_SCAN = 'CHANNEL_SCAN'
    PROCESSING = 'PROCESSING'

    def __str__(self):
        return self.value

# Define SCPI query templates
query_templates = {
    # Commands
    'reset': ['*RST'],  # Reset command
    'measure': [':MEAS?', lambda s: float(s)],  # Measure command

    'clear_log': [':SYST:CLEAR'],  # Clear log command
    'system_error_next': [':SYST:ERR:NEXT?', lambda s: _parse_log_event(s)],  # Get next system error command

    'clear_user_screen': [':DISP:CLEAR'],  # Clear user screen command
    'display_user_text': [lambda line, text: f':DISP:USER{line}:TEXT "{text}"',  # Display user text command
                          lambda line: line if line in {1, 2} else None,
                          lambda text: str(text)],

    # Simple queries
    'detected_line_frequency': [':SYST:LFR?', float],  # Query detected line frequency command

    # Setting of settings
    'set_function': [':SENS:FUNC "{0}"',  # Set function command
                     lambda val: str(val) if str(val) in list(map(str, Function)) else None],
    'set_screen': [':DISP:SCREEN {0}',  # Set screen command
                   lambda val: str(val) if str(val) in list(map(str, Screen)) else None],

    'set_range': [lambda v, mm_func: f':SENS:{mm_func}:RANG {v}' if v != 'auto' else f':SENS:{mm_func}:RANG:AUTO ON',  # Set range command
                  lambda val: val if val == 'auto' or isinstance(val, (float, int)) else None],
}

# Define SCPI sense queries
sense_queries = {
    'set_auto_zero': ['AZER {0}', lambda val: {False: 'OFF', True: 'ON'}.get(val, None)],  # Set auto zero command
    'set_nplc': ['NPLC {0}', lambda val: float(val) if (0.0005 <= float(val) <= 12.0) else None],  # Set NPLC command
}

# Function to transform sense queries
def _sense_queries_transform(template):
    format_func = template[0]
    assert isinstance(format_func, str)
    return [':SENS:{mm_func}:' + format_func] + template[1:]

# Function to combine all queries
def _combined_queries(queries_templates, _sense_queries):
    result = dict()
    result.update(queries_templates)
    result.update(dict((name, _sense_queries_transform(val)) for name, val in _sense_queries.items()))
    return result

# Function to parse log event
def _parse_log_event(s):
    groups = re.fullmatch(r'([+\-\d]+),"(.+)"', s.strip()).groups()
    return int(groups[0]), groups[1]

# Function to generate query text
def query_text(template, mm_state, values):
    formt = template[0]
    rest = template[1:]

    if isinstance(formt, str):
        requires_mm_state = formt.count('{mm_func}') == 1
        no_required_args = formt.count('{') - (1 if requires_mm_state else 0)
    else:
        param_info = inspect.signature(formt).parameters
        requires_mm_state = 'mm_func' in param_info
        no_required_args = len(param_info) - (1 if requires_mm_state else 0)

    parameter_convert_funcs = rest[:no_required_args]

    if no_required_args != len(values):
        raise ValueError

    if len(rest) > no_required_args:
        return_convert = rest[-1]
    else:
        return_convert = None

    query_type = 'write' if return_convert is None else 'query'

    converted_values = [f(v) for f, v in zip(parameter_convert_funcs, values)]
    if None in converted_values:
        raise ValueError

    if isinstance(formt, str):
        return query_type, formt.format(*converted_values, mm_func=mm_state), return_convert
    else:
        if requires_mm_state:
            return query_type, formt(*converted_values, mm_func=mm_state), return_convert
        else:
            return query_type, formt(*converted_values), return_convert

# Combine all query templates
all_query_templates = _combined_queries(query_templates, sense_queries)

# Function to execute query
def do_query(r: MMResourceType, template_name, mm_state, args):
    method, cmd, return_convert = query_text(all_query_templates[template_name], mm_state, args)
    if method == 'write':
        r.write(cmd)
        return None
    elif method == 'query':
        convert = return_convert if return_convert is not None else lambda x: x
        return convert(r.query(cmd))
    else:
        assert False

# Function to connect to the DMM
def connect_to_dmm():
    # Define a default value for resource_address
    resource_address = "USB0::0x05E6::0x6500::04453860::INSTR"
    
    try:
        # Create a resource manager instance
        rm = pyvisa.ResourceManager()
        
        # Try to open a connection to the instrument using the specified resource address
        inst = rm.open_resource(resource_address, timeout=500)  # Set a longer timeout
        
        # Query the instrument to get its identification string
        idn = inst.query('*IDN?')
        
        # Check if the identification string contains 'DMM6500', indicating a Keithley DMM6500
        if 'DMM6500' in idn:
            # If the instrument is identified as a Keithley DMM6500, print the connection port and return the instrument instance
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

# Main function
if __name__ == "__main__":
    # Call the connect_to_dmm function to attempt connection to the DMM
    dmm = connect_to_dmm()

    if dmm:
        # Prompt the user for measurement type, CSV filename, number of samples, and sample interval
        measurement_type = input("What kind of measurement do you want to take (voltage/current/resistance)? ").upper()
        filename = input("Enter the name of the CSV file to save the measurements: ")
        num_samples = int(input("How many samples do you want to take? "))
        sample_interval = float(input("Enter the time interval between samples (in seconds): "))

        # Write header to CSV file
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', measurement_type.capitalize()])

        # Initialize tqdm progress bar
        progress_bar = tqdm(total=num_samples, desc='Progress', unit=' sample', ascii="░▒█")

        # Loop to take measurements and record them to the CSV file
        for _ in range(num_samples):
            measurement = do_query(dmm, 'measure', measurement_type, [])
            if measurement is not None:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                with open(filename, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([timestamp, measurement])
                print(f"{timestamp} - {measurement_type.capitalize()}: {measurement}")
            time.sleep(sample_interval)
            progress_bar.update(1)  # Update progress bar
        progress_bar.close()  # Close progress bar
