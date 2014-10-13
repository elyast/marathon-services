#!/usr/bin/python

import urllib2
import hashlib
import json
import time
import os
import re
import sys

# os.environ['MARATHON_ADDRESS'] = 'hadoop-ha-1:2413'

def _get_url_opener():
  proxy_handler = urllib2.ProxyHandler({})
  opener = urllib2.build_opener(proxy_handler)
  opener.addheaders = [('Accept', 'application/json')]
  return opener

def _get_joined(host, ports):
  return ["{0}:{1}".format(host, port) for port in ports]

def get_hash(string):
  return int(int(hashlib.sha1(string).hexdigest(), 16) % ((1<<31)-1))

http_cli = _get_url_opener()
marathon_adr = os.environ['MARATHON_ADDRESS']

# app_name = 'chronos-service'
def get_app(app_name):
  time_counter = 0
  apps = None
  while apps is None or time_counter > 30:
    marathon_host, marathon_port = marathon_adr.split(':')
    marathon_url = "http://{0}:{1}/v2/apps/{2}".format(marathon_host, marathon_port, app_name)
    try:
      response = http_cli.open(marathon_url)
      apps = json.load(response)
    except Exception as e:
      time.sleep(1)
      time_counter += 1
  hosts = [x['host'] for x in apps['app']['tasks']]
  adrs = {x['host']:x['ports'] for x in apps['app']['tasks']}
  adrs = [_get_joined(host, ports) for host, ports in adrs.iteritems()]
  adrs = map(list, zip(*adrs))
  adrs = [str(','.join(a)) for a in adrs]
  adrs = {"MARATHON_SEED_ADDRESSES_PORT{0}".format(j): adrs[j] for j in range(0,len(adrs))}
  return (hosts, adrs)

def generate_task_id():
  task_str_id = "{0}_{1}_{2}".format(os.environ['MESOS_SLAVE_ID'], os.environ['MESOS_EXECUTOR_ID'], os.environ['PORTS'])
  task_id = get_hash(task_str_id)
  return task_id


if __name__ == "__main__":
  pass
