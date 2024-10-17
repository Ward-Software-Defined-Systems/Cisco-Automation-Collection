# Cisco Multithreaded Configuation Management Automation + M365 Teams Notifications #

Various scripts/apps used for config management:
* <h3>ios-config-backup.py</h2>
  * Used to backup configs from a single or multiple Cisco IOS devices.
* <h3>nxos-config-backup,py</h3>
  * Used to backup configs from a single or multiple Cisco NX-OS devices.
* <h3>configs_to_tftp.py</h3>
  * Ships configs located in the config folders to their corresponding
folders on a TFTP server.
* <h3>More scripts/apps to come...</h3>

### Summary: ###

* Version 1
* Configs are written to .conf file in their corresponding directory:
  * Files are overwritten if they already exist.
* Output is written to the console for monitoring activity.
* Notifications about exceptions are sent to M365 Teams when enabled.
* Configs located in the config folders are uploaded to their
corresponding folders on a TFTP server.
  * Files are overwritten if they already exist.

### Dependencies: ###

* Napalm
* Napalm IOS/NX-OS Device Support (nxos_ssh driver):
  * https://napalm.readthedocs.io/en/latest/support/index.html
* PyMSTeams
* FILE option requires an inventory .csv located in the same directory
as the script/app (an example .csv is provided).
  * Inventory file name can be configured via global variable.
* M365 Teams Messages requires a webhook (disabled by default):
  * https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook?tabs=dotnet
  * The webhook can be configured via global variable.
* TFTP server is used to upload files (disabled by default):
  * The hostname can be configured via global variable.
* .env file is currently being used for secrets
  * You can either use your own .env or another method for passing secrets.

### TODO: ###

I have left TODO comments throughout the code for reference, these are
things I am either still working on or plan to work on and I just 
wanted to call them out as areas of improvement.

* Add additional signal handling
* Add additional formatting such as tittle and sections 
(M365 Teams Messages)
* Exception handling should/could be narrowed down to specific exceptions

### Run: ###

* ./ios-config-backup.py [HOSTNAME | IP | FILE] [USERNAME]
* ./nxos-config-backup.py FILE wsds
* python3 nxos-config-backup.py 10.0.2.2 wsds