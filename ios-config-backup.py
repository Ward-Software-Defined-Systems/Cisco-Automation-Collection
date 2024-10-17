#!/usr/bin/python3

import signal
import sys
import os
import threading
import re
import getpass
import pandas as pd
import csv
import pymsteams
from napalm import get_network_driver
import configs_to_tftp
from dotenv import load_dotenv

load_dotenv()

# Teams Webhook
# When set to '<TEAMS WEBHOOK>', escalating to Teams is disabled.
# Teams messages are only sent when no routing information or an exception is returned.
teams_webhook = '<TEAMS WEBHOOK>'  # os.getenv("TEAMS_WEBHOOK")

# inventory file
inventory_file = './inventory/ios_xe_inventory.csv'

# TFTP Host
# When set to '<TFTP>', TFTP uploading is disabled.
tftp_host = '<TFTP>'  # os.getenv("TFTP_HOST")

# Initializing threads list for multithreading JOIN and semaphore for execution control
threads = []
sema = threading.Semaphore(value=25)


def main(argv):
    if len(argv) < 3:
        help_and_exit(argv[0])
    else:

        # Conditionals for evaluating command line arguments
        if argv[1].upper() == 'FILE':
            inventory = import_inventory(inventory_file)
            password = getpass.getpass('Please enter password: ')
            for index, host in inventory.iterrows():
                # Multithreading for config backup
                sema.acquire()
                config_backup_thread = threading.Thread(target=backup_config,
                                                        args=(host['HOSTNAME'], argv[2], password, host['MGMT IP'], host['NOTES']))
                config_backup_thread.start()
                threads.append(config_backup_thread)

        else:
            backup_config(argv[1], argv[2], getpass.getpass('Please enter password: '))

        for thread in threads:
            # Waiting for threads to complete
            thread.join()

    # Backup configs to TFTP server
    if tftp_host != '<TFTP>':
        configs_to_tftp.ios_configs_to_tftp(tftp_host)


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
    print('Usage: ' + prog + ' [HOSTNAME | IP | FILE] [USERNAME]')
    print('Usage: ' + prog + ' FILE wsds')
    print('Usage: ' + prog + ' 10.0.2.2 wsds')
    print('Usage: ' + prog + 'If the FILE option is used, there should be an inventory .csv file in the same folder '
                             'as the script/app')
    sys.exit(1)


def import_inventory(filename):
    # inventory .csv import
    df = pd.read_csv(filename, skipinitialspace=True, quoting=csv.QUOTE_NONE, engine='python',
                     on_bad_lines='skip').fillna('- -')
    return df


def backup_config(hostname, username, password, mgmt_ip='non-threaded', notes='- -'):
    # Regex used to validate IPv4 address including CDIR format
    # This can be expanded to validate that the IP is within the valid range
    regresult = re.fullmatch('^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$', mgmt_ip)
    if str(regresult) == 'None' and mgmt_ip != 'non-threaded':
        result = 'backup_config(): Invalid IPv4 Address!'
        print(result)
        if teams_webhook != '<TEAMS WEBHOOK>':
            escalate_to_teams(result)
        return

    if mgmt_ip == 'non-threaded':
        driver = get_network_driver("ios")
        device = driver(hostname=hostname, username=username,
                        password=password)  # optional_args = {'port': 8181}
    else:
        driver = get_network_driver("ios")
        device = driver(hostname=mgmt_ip, username=username,
                        password=password)  # optional_args = {'port': 8181}

    try:
        device.open()
        configs = device.get_config()
        device.close()

        # Raw Config Output file
        fh = open('./ios_configs/' + hostname + '.conf', 'w')
        fh.write(configs['running'])
        fh.close()

        if mgmt_ip == 'non-threaded':
            print('Host: ' + hostname + ' (' + '- -' + ') Notes: ' + notes + '\n' + configs['running'] + '\n\n')
        else:
            print('Host: ' + hostname + ' (' + mgmt_ip + ') Notes: ' + notes + '\n' + configs['running'] + '\n\n')

        if mgmt_ip != 'non-threaded':
            sema.release()
    except:
        # TODO: Exception handling should/could be narrowed down to specific exceptions
        result = 'Host: ' + hostname + ' (' + '- -' + ') Notes: ' + notes + '\n' + 'backup_config() Exception: ' + \
                 str(sys.exc_info()[0]) + ', escalating via M365 Teams (if enabled) \n\n'

        print(result)
        if teams_webhook != '<TEAMS WEBHOOK>':
            escalate_to_teams(result)


def escalate_to_teams(message):
    # Send message to Teams channel
    # Used for when no routing information is returned or an exception occurs
    # TODO: Add additional formatting such as tittle and sections
    teams_message = pymsteams.connectorcard(teams_webhook)
    teams_message.text(message)
    teams_message.send()


if __name__ == '__main__':
    main(sys.argv)
