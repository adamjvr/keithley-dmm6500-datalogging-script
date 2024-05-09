import pyvisa

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

if __name__ == "__main__":
    # Call the connect_to_dmm function to attempt connection to the DMM
    dmm = connect_to_dmm()
