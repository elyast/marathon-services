#!/usr/bin/python

import urllib2
import hashlib
import json
import time
import os
import re
import sys
import marathon_client

def file_replace(fname, patterns):
  # pattern is in the file, so perform replace operation.
  with open(fname) as f:
    out_fname = fname + ".tmp"
    out = open(out_fname, "w")
    for line in f:
      for i,j in patterns.iteritems():
        line = line.replace("${%s}" % i,j)
      out.write(line)
    out.close()
    os.rename(out_fname, fname)

if __name__ == "__main__":
  print "Starting of configuration"
  application = sys.argv[1]
  minimum_seeds = int(sys.argv[2])
  config_files = sys.argv[3].split(',')
  seeds_requirement = True
  hosts = []
  adrs = {}
  while seeds_requirement:
    hosts, adrs = marathon_client.get_app(application)
    seeds_requirement = len(hosts) < minimum_seeds
    if seeds_requirement:
      print "Seed requirement not met waiting 5 seconds..."
    else:
      print "Seed requirement met proceeding to launch..."
    time.sleep(5)
  patterns = {"MARATHON_SEED_NODES": str(','.join(hosts)),
              "TASK_ID": str(marathon_client.generate_task_id())}
  patterns.update(adrs)
  patterns.update(os.environ)
  print "All env variables {0}".format(patterns)
  for x in config_files:
    file_replace(x, patterns)
  print "Configuration process ended..."
