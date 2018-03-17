#!/usr/bin/env python

import sys
reload(sys)
sys.setdefaultencoding('utf8')
import requests
import vobject
import re
import time
from asterisk import manager
from requests.auth import HTTPBasicAuth
from lxml import etree
from urlparse import urlparse

# ASTERISK MANAGER CONNECTION
HOST = 'localhost'
PORT = 5038
USER = 'carddavimport'
PASS = 'cidpwd'

# PERSONAL SETTINGS
NATIONALPREFIX = "0049"
DOMESTICPREFIX = "0841"

# get list with links to all available vcards
def getAllVcardLinks(url,auth):
    baseurl = urlparse(url).scheme+'://'+urlparse(url).netloc
    r = requests.request('PROPFIND',url,auth=auth)
    root = etree.XML(r.content)
    vcardUrlList=[]
    for record in root.xpath(".//d:response",namespaces={"d" : "DAV:"}):
	type = record.xpath(".//d:getcontenttype",namespaces={"d" : "DAV:"})
	if (type) and type[0].text.startswith("text/vcard"):
	    vcardlinks = record.xpath(".//d:href",namespaces={"d" : "DAV:"})
	    for link in vcardlinks:
		vcardUrlList.append(baseurl + '/' + link.text);
    return vcardUrlList

def tidyPhoneNumber(num):
    num = re.sub("^\+","00",num)	# +39 -> 0039
    num = re.sub("\D","",num)		# remove all non-digits
    num = re.sub("^"+NATIONALPREFIX+"0*","0",num)	# strip own national prefix
    num = re.sub("^[^0]","0"+DOMESTICPREFIX,num)	# add domestic prefix, if missing

    return num

def main(argv):
    auth = HTTPBasicAuth(argv[2],argv[3])
    url = argv[1]

    # connect to asterisk
    ami = manager.Manager()
    ami.connect(HOST)
    ami.login(USER,PASS)

    # get phone numbers from vcard
    starttime=int(time.time());
    for vurl in getAllVcardLinks(url,auth):
	r = requests.request("GET",vurl,auth=auth)
	vcard = vobject.readOne(r.content)
	if "tel" in vcard.contents:
	    for telno in vcard.contents['tel']:
		num = tidyPhoneNumber(telno.value)
		if "fn" in vcard.contents:
		    name = vcard.fn.value
		    print "Adding/updating Number: "+num+" Name: "+name
		    ami.send_action({"Action": "DBPut", "Family": "cidname", "Key": num, "Val": name})
    ami.logoff()
    ami.close()

if __name__ == "__main__":
    if len(sys.argv)!=4:
	print "Must be called with eight arguments: <carddav-url> <carddav-user> <carddav-password>"
	print "Example: %s https://owncloud.example.com/remote.php/dav/addressbooks/users/russmeyer/contacts/ meyerr p8a55w0rd" % sys.argv[0]
	sys.exit(1)
    sys.exit(main(sys.argv))
