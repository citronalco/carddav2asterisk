# CardDAV-to-Asterisk import

This script reads all contacts from a CardDAV address book and puts them into Asterisk's internal caller id database.
That way Asterisk can show a caller's name instead of just the number.

If there's already an entry in Asterisk's caller database for a specific number, this script updates the number with the new name.

So far I have run this script successfully with OwnCloud 9 to Nextcloud 21 and DAViCal 1.1.10.

### Requirements
* Python 3
* Additional Python 3 modules: requests, vobjects, panoramisk, lxml
  (Install in Debian/Ubuntu/Mint: `apt-get install python3-requests python3-vobject python3-panoramisk python3-lxml`)


### Usage

#### Configuration

1. This script uses Asterisk Manager Interface (AMI) to write to the caller id database, so you need to set up an user with "write" permissions to "system":
To add such an user, create a file `/etc/asterisk/manager.d/carddav2asterisk.conf` like this:

        [carddavimport]
        secret = TopSecret
        permit = 127.0.0.1/255.255.255.0
        write = system
   After creating the file reload Asterisk.


2. Create an ini file like this (you may use the included `example.ini` as a starting point):

        [ami]
        user = carddavimport
        pass = TopSecret
        host = localhost
        port = 5038

        [carddav]
        url = https://nextcloud.example.com/remote.php/dav/addressbooks/users/russmeyer/contacts/
        user = russmeyer
        pass = Evelyn1928

        [phone]
        nationalprefix = 0049
        domesticprefix = 089

   The **[ami]** section must contain the connection parameters to Asterisk Manager Interface.

   The **[carddav]** section must contain the connection parameters to your CardDAV server.

   The **[phone]** section is optional. You may use this to clean up the phone numbers before they get written into Asterisk's database.
   Set ***nationalprefix*** to your national prefix to _remove_ it from phone numbers.
   Set ***domesticprefix*** to your local area code to _add_ it to phone numbers without domestic prefix.
   If in doubt simply omit the **[phone]** section.


3. If you haven't configured CID lookup in Asterisk yet, you may want to add something like this somewhere at the beginning of your dialplan in `extensions.conf`:
``exten => <yourExtension>,n,Set(CALLERID(name)=${IF(${DB_EXISTS(cidname/${CALLERID(num)})}?${DB(cidname/${CALLERID(num)})}:${CALLERID(name)})})``


#### How to run the script
``./carddav2asterisk.py [--no-update] <ini file>``

**Example:**
``./carddav2asterisk.py example.ini``

If you use the `--no-update` switch, the script will not write anything to Asterisk but only show what would be done.

