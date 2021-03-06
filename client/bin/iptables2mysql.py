#! /usr/bin/env python2.7
# -*- coding: UTF8 -*-

from __future__ import print_function

import os, sys
import csv, json
import subprocess
import requests

# my script name with path and any suffix (".py") removed
me = os.path.splitext(os.path.basename(sys.argv[0]))[0]
dbintfile = '/usr/local/opt/pirouter/etc/dbint.json'

# print to stderr
def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

def myexit(exitcode, *args, **kwargs):
  eprint(*args, **kwargs)
  sys.exit(exitcode)

if not os.geteuid() == 0:
  sys.exit("{}: {}: {}".format("ERROR", me, "Script must be run as root"))

# this looks almost like a csv file, in that it has columns
iptablescommand="iptables --zero --numeric --exact --verbose --list FORWARD"
#iptablescommand="cat /Users/kjolley/Dropbox/prj/pirouter/client/pirouter/tmp_rw/iptables.out"

iptablesdata = subprocess.check_output(iptablescommand.split())
reader = csv.reader(iptablesdata.splitlines(), delimiter=' ', skipinitialspace=True)

reader.next()                     # two 'header' lines.  first is chain info.
colnames = reader.next()          # the next row is the column names
hlen = len(colnames)              # how many columns we want in our data
colnames.pop(colnames.index(''))  # remove empty/padding columns

csvrows = []                      # this is the data we will upload

for row in reader:
  if(len(row) < hlen):  continue  # skip informational lines
  if(int(row[1]) == 0): continue  # skip hosts/lines with zero packets
  row.pop(row.index(''))          # remove empty/padding fields
  csvrows.append(dict(zip(colnames, row))) # create a json row and append it to csvrows

# don't bother to try to upload an empty data set
if(len(csvrows) == 0):
  sys.exit()

with open(dbintfile, 'r') as f:
  dbintfo = json.load(f)

dbintfo['iptables'] = csvrows
url = dbintfo['url'] + '/' +  me

r = requests.post(url, json=dbintfo)
if(r.status_code != 200):
  myexit(3, "{}: {}: bad https call to '{}'. Expected 200, got: {}".format("ERROR", me, url, r.status_code))
