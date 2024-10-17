#!/usr/bin/python3

import os
import tftpy
from dotenv import load_dotenv

load_dotenv()

def ios_configs_to_tftp(tftp_host):
    client = tftpy.TftpClient(tftp_host, 69)
    dir_list = os.listdir('./ios_configs')
    for file in dir_list:
        client.upload('/ios_configs/' + file, './ios_configs/' + file)

def nxos_configs_to_tftp(tftp_host):
    client = tftpy.TftpClient(tftp_host, 69)
    dir_list = os.listdir('./nxos_configs')
    for file in dir_list:
        client.upload('/nxos_configs/' + file, './nxos_configs/' + file)

def configs_to_tftp(tftp_host):
    client = tftpy.TftpClient(tftp_host, 69)

    dir_list = os.listdir('./ios_configs')
    for file in dir_list:
        client.upload('/ios_configs/' + file, './ios_configs/' + file)

    dir_list = os.listdir('./nxos_configs')
    for file in dir_list:
        client.upload('/nxos_configs/' + file, './nxos_configs/' + file)


if __name__ == '__main__':
    configs_to_tftp(tftp_host=os.getenv("TFTP_HOST"))
