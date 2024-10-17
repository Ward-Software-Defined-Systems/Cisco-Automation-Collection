#!/usr/bin/python3

import signal
import sys
import threading
import json
import re
import getpass
import pandas as pd
import csv
import pymsteams
from napalm import get_network_driver

# Teams Webhook
# When set to '<TEAMS WEBHOOK>', escalating to Teams is disabled.
# Teams messages are only sent when no routing information or an exception is returned.
teams_webhook = '<TEAMS WEBHOOK>'

# inventory file
inventory_file = './inventory/nxos_inventory.csv'

# Initializing threads list for multithreading JOIN and semaphore for execution control
threads = []
sema = threading.Semaphore(value=25)


def main(argv):

    if len(argv) < 4:
        help_and_exit(argv[0])
    else:

        # Raw Output file (flushed after each write)
        # TODO: Add additional formatting and/or processing for the output file
        fh = open('output/route_reachability.output', 'w')

        # TODO: Add additional input validation to be performed prior to evaluating conditions

        # Conditionals for evaluating command line arguments
        if (argv[2].upper() == 'ALL') and (argv[1].upper() != 'FILE'):
            # Hostname and route table options selected

            result = 'Host: ' + argv[1] + ' (' + '- -' + ') Notes: ' + '- -' + \
                     '\n' + get_route_table(argv[1], argv[3], getpass.getpass('Please enter password: ')) + '\n\n'
            print(result)
            fh.write(result)
            fh.flush()

            if 'no routing information' in result.lower() or 'exception' in result.lower() or 'route not found' in result.lower():
                # If no routing information or an exception is returned, send Teams message

                if teams_webhook != '<TEAMS WEBHOOK>':
                    escalate_to_teams(result)

        elif (argv[1].upper() == 'FILE') and (argv[2].upper() != 'ALL'):
            # inventory file  and destination prefix options selected

            inventory = import_inventory(inventory_file)
            passwd = getpass.getpass('Please enter password: ')
            for index, host in inventory.iterrows():
                # Multithreading for route check

                sema.acquire()
                route_check_thread = threading.Thread(target=threaded_route_check,
                                                      args=(fh, host['HOSTNAME'],
                                                            host['MGMT IP'], host['NOTES'], argv[2], argv[3], passwd))
                route_check_thread.start()
                threads.append(route_check_thread)

        elif (argv[1].upper() == 'FILE') and (argv[2].upper() == 'ALL'):
            # inventory file and route table options selected

            inventory = import_inventory(inventory_file)
            passwd = getpass.getpass('Please enter password: ')
            for index, host in inventory.iterrows():
                # Multithreading for route table check

                sema.acquire()
                route_check_thread = threading.Thread(target=threaded_route_table_check,
                                                      args=(fh, host['HOSTNAME'],
                                                            host['MGMT IP'], host['NOTES'], argv[3], passwd))
                route_check_thread.start()
                threads.append(route_check_thread)

        else:
            # Hostname and destination prefix option selected

            result = 'Host: ' + argv[1] + ' (' + '- -' + ') Notes: ' + '- -' + \
                     '\n' + get_route(argv[1], argv[2], argv[3], getpass.getpass('Please enter password: ')) + '\n\n'
            print(result)
            fh.write(result)
            fh.flush()

            if 'no routing information' in result.lower() or 'exception' in result.lower() or 'route not found' in result.lower():
                # If no routing information or an exception is returned, send Teams message

                if teams_webhook != '<TEAMS WEBHOOK>':
                    escalate_to_teams(result)

        for thread in threads:
            # Waiting for threads to complete

            thread.join()

        # Closing output file
        fh.close()


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

    print('Usage: ' + prog + ' [HOSTNAME | FILE] [DESTINATION IPv4 or CDIR | ALL] [USERNAME]')
    print('Usage: ' + prog + ' FILE ALL wsds')
    print('Usage: ' + prog + ' router.wsds.io ALL wsds')
    print('Usage: ' + prog + ' FILE 10.2.3.0/24 wsds')
    print('Usage: ' + prog + ' router.wsds.io 10.2.3.0/24 wsds')
    print('Usage: ' + prog + ' If you use the FILE option, there should be an inventory .csv file in the same folder '
                             'as the script (filename can be set within the script using Global Variable)')
    sys.exit(1)


def import_inventory(filename):
    # Uses Pandas to read CSV into data frame

    df = pd.read_csv(filename, skipinitialspace=True, quoting=csv.QUOTE_NONE, engine='python',
                     on_bad_lines='skip').fillna('- -')
    return df


def threaded_route_check(file_handle, mgmt_host, mgmt_ip, mgmt_notes, destination, username, password):
    # Wrapper for threaded execution of the route checks

    result = 'Host: ' + mgmt_host + ' (' + mgmt_ip + ') Notes: ' + mgmt_notes + \
             '\n' + str(get_route(mgmt_ip, destination, username, password)) + '\n\n'
    print(result)
    file_handle.write(result)
    file_handle.flush()
    if 'no routing information' in result.lower() or 'exception' in result.lower() or 'route not found' in result.lower():
        if teams_webhook != '<TEAMS WEBHOOK>':
            escalate_to_teams(result)

    sema.release()

def threaded_route_table_check(file_handle, mgmt_host, mgmt_ip, mgmt_notes, username, password):
    # Wrapper for threaded execution of the route table checks

    result = 'Host: ' + mgmt_host + ' (' + mgmt_ip + ') Notes: ' + mgmt_notes + \
             '\n' + str(get_route_table(mgmt_ip, username, password)) + '\n\n'
    print(result)
    file_handle.write(result)
    file_handle.flush()
    if 'no routing information' in result.lower() or 'exception' in result.lower() or 'route not found' in result.lower():
        if teams_webhook != '<TEAMS WEBHOOK>':
            escalate_to_teams(result)

    sema.release()

def escalate_to_teams(message):
    # Send message to Teams channel
    # Used for when no routing information is returned or an exception occurs
    # TODO: Add additional formatting such as tittle and sections

    teams_message = pymsteams.connectorcard(teams_webhook)
    teams_message.text(message)
    teams_message.send()


def get_route_table(wsds_device, user, passwd):
    # Retrieves the route table from the specified device

    driver = get_network_driver("nxos_ssh")
    device = driver(hostname=wsds_device, username=user,
                    password=passwd, optional_args={'read_timeout_override': 120})  # optional_args = {'port': 8181}
    try:
        device.open()
        route_details = device.cli(['sh ip route'])['sh ip route']
        device.close()
        return route_details
    except:
        # TODO: Exception handling should/could be narrowed down to specific exceptions
        return 'get_route_table() Exception: ' + str(sys.exc_info()[0]) + ', escalating via M365 Teams (if enabled)'


def get_route(wsds_device, destination, user, passwd):
    # Retrieves routes for the specified device and prefix

    # Regex used to validate IPv4 address including CDIR format
    # This can be expanded to validate that the IP is within the valid range
    regresult = re.fullmatch('^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$', destination)
    if str(regresult) == 'None':
        return 'get_route(): Invalid IPv4 Address!'
    else:
        driver = get_network_driver("nxos_ssh")
        device = driver(hostname=wsds_device, username=user,
                        password=passwd, optional_args={'read_timeout_override': 120})  # optional_args = {'port': 8181}
        try:
            device.open()
            # FIXME: device.get_route_to(destination) persistently returns an empty dictionary, using device.cli()
            #  for now
            route_details = device.cli(['sh ip route ' + destination])['sh ip route ' + destination]
            device.close()

            if len(route_details) == 0:
                return 'No routing information for destination ' + destination + ', escalating via M365 Teams (if ' \
                                                                                 'enabled)'
            elif len(route_details) == 1:
                for route_key in route_details:
                    if not route_details[route_key]:
                        return 'No routing information for destination ' + route_key + ', escalating via M365 Teams ' \
                                                                                       '(if enabled)'
                else:
                    return route_details  # json.dumps(route_details, sort_keys=True, indent=4)
            elif 'route not found' in route_details.lower():
                return 'No routing information for destination ' + destination + ', escalating via M365 Teams (if ' \
                                                                                 'enabled)'
            else:
                return route_details  # json.dumps(route_details, sort_keys=True, indent=4)
        except:
            # TODO: Exception handling should/could be narrowed down to specific exceptions
            return 'get_route() Exception: ' + str(sys.exc_info()[0]) + ', escalating via M365 Teams (if enabled)'


if __name__ == '__main__':
    main(sys.argv)
