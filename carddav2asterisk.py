#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import requests
import vobject
import re
import asyncio
import time
from panoramisk import Manager
from requests.auth import HTTPBasicAuth
from lxml import etree
from urllib.parse import urlparse
import argparse
import configparser


# get list with links to all available vcards
def getAllVcardLinks(url, auth):
  baseurl = urlparse(url).scheme + '://' + urlparse(url).netloc

  r = requests.request('PROPFIND', url, auth = auth, headers={'content-type': 'text/xml', 'Depth': '1'})
  if r.status_code != 207:
    raise RuntimeError('error in response from %s: %r' % (url, r))

  vcardUrlList = []
  root = etree.XML(r.text.encode())
  for link in root.xpath('./d:response/d:propstat/d:prop/d:getcontenttype[starts-with(.,"text/vcard")]/../../../d:href', namespaces = {"d": "DAV:"}):
    vcardUrlList.append(baseurl + link.text)
  return vcardUrlList


def tidyPhoneNumber(config, num):
  num = re.sub("^\+", "00", num)    # +39 -> 0039
  num = re.sub("\D", "", num)       # remove all non-digits
  if 'phone' in config:
    if 'nationalprefix' in config['phone']:
      num = re.sub("^" + config['phone']['nationalprefix'] + "0*", "0", num)    # strip own national prefix
    if 'domesticprefix' in config['phone']:
      num = re.sub("^[^0]", "0" + config['phone']['domesticprefix'], num)       # add domestic prefix, if missing
  return num


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('ini_file')
  parser.add_argument("--no-update", help="Don't write to asterisk", action='store_true', default=False)
  parser.add_argument("--sleep", help="Sleep SLEEP seconds between carddav calls", action='store', type=float, default=0)
  args = parser.parse_args()

  config = configparser.RawConfigParser()
  config.read(args.ini_file)

  loop = asyncio.get_event_loop()
  loop.run_until_complete(putCids(loop, args, config))
  loop.close()


def putCids(lp, args, config):
  auth = HTTPBasicAuth(config['carddav']['user'], config['carddav']['pass'])
  url = config['carddav']['url']

  # connect to asterisk
  ami = Manager(host = config['ami']['host'],
                  port = config['ami']['port'],
                  username = config['ami']['user'],
                  secret = config['ami']['pass'])
  yield from ami.connect()

  # get phone numbers from vcard
  for vurl in getAllVcardLinks(url, auth):
    r = requests.request("GET", vurl, auth=auth)
    try:
      vcard = vobject.readOne(r.text)
      time.sleep(args.sleep)
    except ParseError as e:
      print(e)
      continue
    if "tel" in vcard.contents:
      for telno in vcard.contents['tel']:
        num = tidyPhoneNumber(config, telno.value)
        if num and "fn" in vcard.contents:
          name = vcard.fn.value
          print("Adding/updating Number: %s Name: %s" % (num, name), end="... ")
          if not args.no_update:
            ami_result = yield from ami.send_action({"Action": "DBPut", "Family": "cidname", "Key": num, "Val": name})
            print(ami_result.Response)
          else:
            print("no-update")
  ami.close()

if __name__ == "__main__":
  main()
