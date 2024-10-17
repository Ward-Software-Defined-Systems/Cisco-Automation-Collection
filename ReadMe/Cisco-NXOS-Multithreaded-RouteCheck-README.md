# Cisco NX-OS Multithreaded Route Check (IPv4) + M365 Teams Notifications #

Every now and then reachability to other networks/subnets needs to be 
checked. Obviously, there are things you can do like using PING or 
TRACEROUTE to investigate the issue but sometimes you end up having to
double-check routes on your L3 network devices 
(routers and/or L3 switches). 

If you are managing a small network with a single router, it is pretty
straight forward to check for the existence of a route in the routing 
table. However, if you have to check hundreds of devices this task
quickly becomes impossible to accomplish.

Cue Automation!

I created this automation script/app to accomplish the task of checking 
for a specific route or reviewing the entire route table of multiple 
devices or even a single device if that's what you want to do.

Whenever there is an exception generated, related to connecting to and 
retrieving routing information, it is displayed and can also be sent to 
a Microsoft 365 Teams Channel for escalation, this includes a route that 
is not found.

When checking multiple devices, multithreading is utilized for
performance and file writes are flushed frequently.

### Summary: ###

* Version 1
* Used to check the existence of a route or the routing table on a single 
or multiple Cisco NX-OS devices.
* Output it written to the console and to a route_reachability.txt file.
* Notifications about exceptions and missing routes are sent to 
M365 Teams when enabled.

### Dependencies: ###

* Napalm
* Napalm NX-OS Device Support (nxos_ssh driver):
  * https://napalm.readthedocs.io/en/latest/support/index.html
* PyMSTeams
* FILE option requires an inventory .csv located in the same directory
as the script/app. An example .csv is provided.
  * Inventory file name can be configured via global variable.
* M365 Teams Messages requires a webhook (disabled by default):
  * https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook?tabs=dotnet
  * The webhook can be configured via global variable.

### TODO: ###

I have left TODO comments throughout the code for reference, these are
things I am either still working on or plan to work on and I just 
wanted to call them out as areas of improvement.

* Add additional formatting and/or processing for the output file
* Add additional input validation to be performed prior to evaluating conditions
* Add additional signal handling
* Add additional formatting such as tittle and sections 
(M365 Teams Messages)
* Exception handling should/could be narrowed down to specific exceptions

### Run: ###

* ./NXOS-Multithreaded-RouteCheck.py [HOSTNAME | FILE] [DESTINATION IPv4 or CDIR | ALL] [USERNAME]
* ./NXOS-Multithreaded-RouteCheck.py FILE ALL wsds
* ./NXOS-Multithreaded-RouteCheck.py router.wsds.io ALL wsds
* ./NXOS-Multithreaded-RouteCheck.py FILE 10.2.3.0/24 wsds
* ./NXOS-Multithreaded-RouteCheck.py router.wsds.io 10.2.3.0/24 wsds
* python3 NXOS-Multithreaded-RouteCheck.py router.wsds.io 10.2.3.3 wsds