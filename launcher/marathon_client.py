#!/usr/bin/python

import urllib2
import hashlib
import json
import time
import os
import re
import sys
import socket

def _get_url_opener():
  proxy_handler = urllib2.ProxyHandler({})
  opener = urllib2.build_opener(proxy_handler)
  opener.addheaders = [('Accept', 'application/json')]
  return opener

def _get_joined(host, ports):
  return ["{0}:{1}".format(host, port) for port in ports]

def get_hash(string):
  return int(int(hashlib.sha1(string).hexdigest(), 16) % ((1<<31)-1))

def _get_marathon_response(http_cli, marathon_address, app_name):
  for t in range(0,10):
    try:
      marathon_url = "http://{0}/v2/apps/{1}".format(marathon_address, app_name)
      response = http_cli.open(marathon_url)
      apps = json.load(response)
      print "Got: {0}".format(apps)
      return apps
    except Exception as e:
      print "Got: {0}".format(e)
      time.sleep(3)
  return {}

# app_name = 'redis'
# marathon_address = 'hadoop-ha-1:8773'
def get_app_tasks(marathon_address, app_name):
  http_cli = _get_url_opener()
  tasks = _get_marathon_response(http_cli, marathon_address, app_name)
  if len(tasks) == 0:
    return []
  tasks = [{'host':x['host'], 'ip':socket.gethostbyname(x['host']), 'ports': x['ports'], 'stagedAt': x['stagedAt']} for x in tasks['app']['tasks']]
  tasks = sorted(tasks, key=lambda t: t['stagedAt'])
  return tasks

def generate_task_id():
  task_str_id = "{0}_{1}_{2}".format(os.environ['MESOS_SLAVE_ID'], os.environ['MESOS_EXECUTOR_ID'], os.environ['PORTS'])
  task_id = get_hash(task_str_id)
  return task_id

def get_hosts(tasks):
  return [x['host'] for x in tasks]

# attribute = 'host'
# attribute = 'ip'
def get_addresses_by(tasks, attribute='host'):
  adrs = [_get_joined(adr[attribute], adr['ports']) for adr in tasks]
  adrs = map(list, zip(*adrs))
  adrs = [str(','.join(a)) for a in adrs]
  return {"TASK_{1}_PORT{0}".format(j, attribute.upper()): adrs[j] for j in range(0,len(adrs))}


if __name__ == "__main__":
  pass
