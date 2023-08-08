"""
Author:	Jack Connor
Date Created: 2020

This program sends a command to a serial device at a fixed frequency causing that device to switch on or off.
The device begins in the off state. Upon receipt of the command, the device switches to the other state.
The switching schedule can be overriden manually.

This program is run out of the main function and split among four other functions.
"""

import serial
import time
import datetime
import msvcrt
import os
import pandas as pd
from os import path

def get_date_string():
    """
    Uses clock to make a date string.
    Note, this could be done with:
        datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d')
    Args:
        None
    Returns:
        date_string (string): string with date formated yyyymmdd
    """
    # Obtain year, month, and day.
    Y = str(datetime.datetime.now().year)
    m =str(datetime.datetime.now().month)
    d =str(datetime.datetime.now().day)

    # Zero pad month.
    if datetime.datetime.now().month < 10:
        _m = "0"
    else:
        _m = ""

    # Zero pad day.
    if datetime.datetime.now().day < 10:
        _d = "0"
    else:
        _d = ""

    # Combine year, month, and day into string.
    date_string = Y + _m + m + _d + d
    return date_string

def get_timestamp(current_time):
    """
    Uses clock to make a timestamp.
    Args:
        current_time (datetime.datetime): datetime object representing current time
    Returns:
        string containing timestamp
    """
    return datetime.datetime.strftime(current_time, "%Y-%m-%d %H:%M:%S")

def change_system_state(ser, toggle, dic, command_cycle_period, writeFile):
    """
    Changes the solenoid state, maintains a table of solenoid state changes, and schedules the next state change.
    Args:
        ser (serial.Serial): object representing the serial connection to the solenoid controller
        toggle (int): integer representing the current state of the solenoids
            0: Off
            1: On
        dic (dict): System State Table; table listing times of solenoid changes and the states the solenoids were changed to
        command_cycle_period (float): period in minutes for issuing state change commands to the solenoids
        writeFile (str): filename for writing System State Table
    Returns:
        writes commands to solenoid controller
        toggle (int): integer representing the current state of the solenoid; updated to reflect new state change
            0: Off
            1: On
        dic (dict): System State Table; table listing times of solenoid changes and the states the solenoids were changed to
            updated to reflect new state change
        last_state_change_time (float): time (in seconds since the epoch) of the last command sent to the solenoid controller
    """
    # Send a command to the solenoid controller telling it to change the solenoid state.
    cmd = b'0'
    ser.write(cmd)

    # Record the time of the state change. This will be used to schedule the next state change.
    last_state_change_time = time.time()

    # Generate a timestamp.
    current_time = datetime.datetime.now()
    timestamp = get_timestamp(current_time)

    # Add the timestamp to a new row in the System State Table.
    dic['Timestamp'] += [timestamp]

    # Use the cycle period to determine the next state change time. This is for reporting to the console, not for scheduling.
    next_state_change_time = current_time + datetime.timedelta(minutes=command_cycle_period)

    # Follow these steps if the solenoid was changed from an "On" state.
    if toggle:
        # Add "Off" to the newest row in the System State Table.
        dic['System State'] += ['Off']

        # Write the System State Table to CSV, clear the console and print the System State Table to the console.
        df = pd.DataFrame(dic) 
        df.to_csv(writeFile, index=False)
        os.system('cls')
        print(df)

        # Set the toggle parameter to 0 indicating that the system is in the "Off" state.
        toggle = 0

        # Print a message to the console.
        print(f'\nSystem Deactivated.\nSystem will automatically activate at {get_timestamp(next_state_change_time)}, or press 0 to activate system.\n')

    # Follow these steps if the solenoid was changed from an "Off" state.
    else:
        # Add "Off" to the newest row in the System State Table.
        dic['System State'] += ['On']

        # Write the System State Table to CSV, clear the console and print the System State Table to the console.
        df = pd.DataFrame(dic) 
        df.to_csv(writeFile, index=False)
        os.system('cls')
        print(df)

        # Set the toggle parameter to 1 indicating that the system is in the "On" state.
        toggle = 1

        # Print a message to the console.
        print(f'\nSystem Activated.\nSystem will automatically deactivate at {get_timestamp(next_state_change_time)}, or press 0 to deactivate system.\n')

    return toggle, dic, last_state_change_time

def logger(port, baud, command_cycle_period, writeFile):
    """
    Controls and logs solenoid activation cycling.
    Args:
        port (str): string representing COM port designation for solenoid controller
        baud(int): solenoid controller baud rate
        command_cycle_period (float): period in minutes for changing the solenoid state
        writeFile (str): filename to write System State Table
    Returns:
        controls and logs solenoid activation cycling
    """
    # Initialize a serial connection and a serial connection object for the solenoid controller.
    ser = serial.Serial(port, baud)

    # Initialize toggle parameter to 0, indicating the "Off" state.
    toggle = 0

    # Initialize System State Table.
    dic = {'Timestamp': [], 'System State': []} 

    # Prompt the user to begin the solenoid switching cycle.
    print('Press Enter to initiate activation cycling.\n')

    # Process user input.
    cmd = input()
    while cmd != '':
        print('Press Enter to initiate activation cycling.\n')
        cmd = input()
    time.sleep(1)

    # Initiate and log the first solenoid state change.
    toggle, dic, last_state_change_time = change_system_state(ser, toggle, dic, command_cycle_period, writeFile)

    # Loop through 19 more solenoid state change cycles.
    cycle_n = 1
    while cycle_n < 20:
        time.sleep(0.01)
        # Listen for keyboard command to manually override automatic cycling.
        if msvcrt.kbhit():
            cmd = msvcrt.getch()
            if cmd == b'0':
                toggle, dic, last_state_change_time = change_system_state(ser, toggle, dic, command_cycle_period, writeFile)
        # If the command_cycle_period has elapsed since the last solenoid state change, intiate a solenoid state change.
        elif time.time() - last_state_change_time >= command_cycle_period*60:
            toggle, dic, last_state_change_time = change_system_state(ser, toggle, dic, command_cycle_period, writeFile)
            cycle_n += 1

    # Add a final row to the System State Table with a timestamp 1/2 of the command cycle period following the last solenoid state change.
    # This is used for data processing.
    last_ts = datetime.datetime.now() + datetime.timedelta(seconds = command_cycle_period*60/2)
    dic['Timestamp'] += [get_timestamp(last_ts)]
    dic['System State'] += ['On']

    # Write the final System State Table.
    pd.DataFrame(dic).to_csv(writeFile, index=False)

def main():
    """
    Parses command line arguments, creates initial user interface, calls logger function.
    Args:
        command line arguments described in function
    Returns:
        establishes required parameters and runs logger
    """

    # Import library for parsing command line arguments.
    import argparse

    # Initialize argument parser.
    parser = argparse.ArgumentParser(description='COM and Data Writing Settings')
    # Create an argument to specify file writing directory and provide a default.
    parser.add_argument('-d', '--write_dir', type=str, help='Directory to save datafile', default='C:\\Data\\TSLog\\')
    # Create an argument to specify solenoid controller baud rate and provide a default.
    parser.add_argument('-b', '--baud', type=int, help='Baud rate', default = 9600)
    # Create an argument to specify solenoid controller COM port and provide a default.
    parser.add_argument('-c', '--COM_Port', type=str, help='COM port to open', default = 'COM3')
    # Create an argument to specify activation cycle period and provide a default. This is the period of the entire on/off cycle.
    parser.add_argument('-p', '--cycle_period', type=str, help='Activation Cycle Period (Minutes)', default = '2')
    # Parse arguments.
    args = parser.parse_args()

    # Set parsed arguments to variables.
    write_directory = args.write_dir
    port = args.COM_Port
    baud = args.baud
    command_cycle_period = float(args.cycle_period)/2 # Command cycle period is the period at which commands will be sent to the solenoid controller. This is 1/2 of the activation cycle.

    # Set a default writefile name.
    datestring = get_date_string()
    writeFile = write_directory + datestring + '_log.csv'

    # Give the user the option to change the default writefile name.
    print('Would you like to write to {}? y/n'.format(writeFile))
    answer = input()
    if answer == 'y':
        print("\nCreating new file: " +  writeFile + '\n')
    else:
        print("Enter a filename suffix.")
        suffix = input()
        writeFile = '{}_{}.csv'.format(writeFile[:-4], suffix)
        print("\nCreating new file: " +  writeFile + '\n')

    # Run the logger function.
    logger(port, baud, command_cycle_period, writeFile)

# Run the main function upon execution of this python script.
if __name__ == '__main__':
    main()
