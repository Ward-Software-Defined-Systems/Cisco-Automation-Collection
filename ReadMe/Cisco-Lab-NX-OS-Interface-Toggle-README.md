# Cisco NX-OS 9000v Interface Toggle #

This is specific to a lab environment, and specifically Cisco Modeling Labs, sometimes pst boot the NX-OS 9000v Ethernet
interfaces are shutdown despite the being configured in the running config as UP (No Shutdown).

THis script/app can be used to toggle the interfaces, shutdown and then no shutdown, to bring them up (helps if you
you have a lot of 9000v devices in your workbench).

### Summary: ###

* Version 1

### Dependencies: ###

* Napalm
* Napalm NX-OS Device Support (nxos_ssh driver):
  * https://napalm.readthedocs.io/en/latest/support/index.html
* Inventory file name can be configured via global variable.
* Username and Password are sourced from .env file.

### Run: ###

* ./nxos-interface-toggle.py
* python3 nxos-interface-toggle.py