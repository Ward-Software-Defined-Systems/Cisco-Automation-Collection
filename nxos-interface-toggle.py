#!/usr/bin/python3

import signal
import sys
import os
import threading
import re
import pandas as pd
import csv
from napalm import get_network_driver
from dotenv import load_dotenv

load_dotenv()

# inventory file
inventory_file = './inventory/nxos_inventory.csv'

# Initializing threads list for multithreading JOIN and semaphore for execution control
threads = []
sema = threading.Semaphore(value=25)


def main(argv):
    inventory = import_inventory(inventory_file)

    toggle_interfaces(inventory.iloc[0]['HOSTNAME'], os.getenv("USERNAME"), os.getenv("PASSWORD"),
                      inventory.iloc[0]['MGMT IP'], inventory.iloc[0]['NOTES'])

    for index, host in inventory.iterrows():
        # Multithreading for config backup
        if host['HOSTNAME'] == 'NXOS9K-MGMTL2':
            continue

        sema.acquire()
        toggle_thread = threading.Thread(target=toggle_interfaces, args=(host['HOSTNAME'], os.getenv("USERNAME"),
                                                                         os.getenv("PASSWORD"), host['MGMT IP'],
                                                                         host['NOTES']))
        toggle_thread.start()
        threads.append(toggle_thread)

    for thread in threads:
        # Waiting for threads to complete
        thread.join()

def handler(signum, frame):
    # Signal handler
    # I am really only using the to catch Ctrl-C and prompt
    # This can be expanded and a more "graceful" exit can be performed
    # TODO: Add additional signal handling
    print('\nSIGNUM: ' + str(signum) + '\n' + 'FRAME: ' + str(frame) + '\n')
    res = input("Ctrl-c was pressed. Do you want to exit? y/n ")
    if res == 'y':
        exit(1)


# Registering signal handler
signal.signal(signal.SIGINT, handler)


def help_and_exit(prog):
    # Usage print when invalid number of command line arguments are provided
    print('Usage: ' + prog)
    sys.exit(1)


def import_inventory(filename):
    # inventory .csv import
    df = pd.read_csv(filename, skipinitialspace=True, quoting=csv.QUOTE_NONE, engine='python',
                     on_bad_lines='skip').fillna('- -')
    return df


def toggle_interfaces(hostname, username, password, mgmt_ip='non-threaded', notes='- -'):
    # Regex used to validate IPv4 address including CDIR format
    # This can be expanded to validate that the IP is within the valid range
    regresult = re.fullmatch('^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$', mgmt_ip)
    if str(regresult) == 'None' and mgmt_ip != 'non-threaded':
        result = 'backup_config(): Invalid IPv4 Address!'
        print(result)
        return

    driver = get_network_driver("nxos_ssh")
    device = driver(hostname=mgmt_ip, username=username,
                    password=password, optional_args={'read_timeout_override': 120})  # optional_args = {'port': 8181}

    try:
        if hostname == 'NXOS9K-MGMTL2':
            device.open()
            device.load_merge_candidate('./nxos-merge-configs/int_et1-1-11_shut.conf')
            device.commit_config()
            # if device.has_pending_commit():
            #    device.confirm_commit()

            device.load_merge_candidate('./nxos-merge-configs/int_et1-1-11_noshut.conf')
            device.commit_config()
            # if device.has_pending_commit():
            #    device.confirm_commit()
            device.close()
            result = 'Toggled int et1/1-11 shut/no shut'
            print('Host: ' + hostname + ' (' + mgmt_ip + ') Notes: ' + notes + '\n' + str(result) + '\n\n')
        else:
            device.open()
            device.load_merge_candidate('./nxos-merge-configs/int_et1-1-7_shut.conf')
            device.commit_config()
            # if device.has_pending_commit():
            #    device.confirm_commit()

            device.load_merge_candidate('./nxos-merge-configs/int_et1-1-7_noshut.conf')
            device.commit_config()
            # if device.has_pending_commit():
            #    device.confirm_commit()
            device.close()
            result = 'Toggled int et1/1-7 shut/no shut'
            print('Host: ' + hostname + ' (' + mgmt_ip + ') Notes: ' + notes + '\n' + str(result) + '\n\n')

        sema.release()
    except:
        # TODO: Exception handling should/could be narrowed down to specific exceptions
        result = 'Host: ' + hostname + ' (' + mgmt_ip + ') Notes: ' + notes + '\n' + 'toggle_interfaces() Exception: ' + \
                 str(sys.exc_info()[0]) + '\n\n'
        print(result)


if __name__ == '__main__':
    main(sys.argv)
