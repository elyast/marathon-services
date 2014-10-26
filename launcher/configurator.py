#!/usr/bin/python

import urllib2
import hashlib
import json
import time
import os
import re
import sys
import math
import marathon_client
import socket

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

def what_is_my_ip():
  return socket.gethostbyname(socket.getfqdn())

# minimum_seeds_ratio = float("0.3")
# application = 'redis'
# instances = 1
# os.environ['MARATHON_ADDRESS'] = 'hadoop-ha-1:8773'
if __name__ == "__main__":
  print "Starting of configuration"
  application = sys.argv[1]
  minimum_seeds_ratio = float(sys.argv[2])
  config_files = sys.argv[3].split(',')
  marathon_address = os.environ['MARATHON_ADDRESS']
  instances = marathon_client.get_app_instances(marathon_address, application)
  minimum_seeds = int(math.ceil(minimum_seeds_ratio * instances))
  task_no = 0
  tasks = []
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
              "MARATHON_ALL_NODES": str(','.join(hosts)),
              "CURRENT_TASK_NO": str(task_no),
              "SEED_TASK_NO": str(minimum_seeds),
              "MY_IP": str(what_is_my_ip()),
              "REQUESTED_INSTANCES": str(instances),
              "TASK_ID": str(marathon_client.generate_task_id())}
  patterns.update(marathon_client.get_addresses_by(tasks[:minimum_seeds], 'host', "MARATHON_SEED"))
  patterns.update(marathon_client.get_addresses_by(tasks[:minimum_seeds], 'ip', "MARATHON_SEED"))
  patterns.update(marathon_client.get_addresses_by(tasks, 'host', "MARATHON_ALL"))
  patterns.update(marathon_client.get_addresses_by(tasks, 'ip', "MARATHON_ALL"))
  patterns.update(os.environ)
  print "All env variables {0}".format(patterns)
  for x in config_files:
    file_replace(x, patterns)
  print "Configuration process ended..."
