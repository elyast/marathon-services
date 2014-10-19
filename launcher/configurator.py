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


# minimum_seeds = 3
# application = 'redis'
# os.environ['MARATHON_ADDRESS'] = 'hadoop-ha-1:8773'
if __name__ == "__main__":
  print "Starting of configuration"
  application = sys.argv[1]
  minimum_seeds = int(sys.argv[2])
  config_files = sys.argv[3].split(',')
  marathon_address = os.environ['MARATHON_ADDRESS']
  task_no = 0
  while task_no < minimum_seeds:
    tasks = marathon_client.get_app_tasks(marathon_address, application)
    task_no = len(tasks)
    if task_no < minimum_seeds:
      print "Seed requirement not met waiting 5 seconds..."
    else:
      print "Seed requirement met proceeding to launch..."
    time.sleep(5)
  hosts = marathon_client.get_hosts(tasks)
  patterns = {"MARATHON_SEED_NODES": str(','.join(hosts[:minimum_seeds])),
              "CURRENT_TASK_NO": str(task_no),
              "TASK_ID": str(marathon_client.generate_task_id())}
  patterns.update(marathon_client.get_addresses_by(tasks[:minimum_seeds], 'host'))
  patterns.update(marathon_client.get_addresses_by(tasks[:minimum_seeds], 'ip'))
  patterns.update(os.environ)
  print "All env variables {0}".format(patterns)
  for x in config_files:
    file_replace(x, patterns)
  print "Configuration process ended..."
