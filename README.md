# CardDAV-to-Asterisk import

This script reads all contacts from a CardDAV addressbook and puts them into Asterisk's internal caller id database.
That way Asterisk can show a caller's name instead of just the number.

If there's already an entry in Asterisk's caller database for a specific number, this script updates the number with the new name.
So far I have only tested with OwnCloud 9.

### Usage

#### Configuration
1. This script uses Asterisk Manager to access the caller id database, so you need to set up an user with "system" permissions if you have not already done so. To add an user create the file "/etc/asterisk/manager.d/carddav2asterisk.conf":
```[carddavimport]
secret = cidpwd
permit = 127.0.0.1/255.255.255.0
read = system
write = system```
1. Open the script in an editor and edit the user's credentials and host and port of Asterisk's Manager interface:```
# ASTERISK MANAGER CONNECTION
HOST = 'localhost'
PORT = 5038
USER = 'carddavimport'
PASS = 'cidpwd'```
1. Change NATIONALPREFIX and DOMESTICPREFIX to match your location:```
# PERSONAL SETTINGS
NATIONALPREFIX = "0049"
DOMESTICPREFIX = "0841"```
1. If you haven't configured CID lookup in Asterisk yet, you may want to add something like this somewhere at the beginning of your dialplan in extensions.conf: ``exten => <yourExtension>,n,Set(CALLERID(name)=${IF(${DB_EXISTS(cidname/${CALLERID(num)})}?${DB(cidname/${CALLERID(num)})}:${CALLERID(name)})})``

#### How to run the script
``./carddav2asterisk.py <URl to CardDAV addressbook> <username> <password>``

Example:
``./carddav2asterisk.py https://owncloud.example.com/remote.php/dav/addressbooks/users/russmeyer/contacts/ meyerr p8a55w0rd``
