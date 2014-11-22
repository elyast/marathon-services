#!/usr/bin/python

import hashlib
import time
import os
import re
import sys
import socket
import marathon

def _get_joined(host, ports):
  return ["{0}:{1}".format(host, port) for port in ports]

def get_hash(string):
  return int(int(hashlib.sha1(string).hexdigest(), 16) % ((1<<31)-1))

def _get_marathon_response(marathon_addresses, app_name):
  m_adrs = marathon_addresses.split(',')
  for t in range(0,5):
    cli = marathon.MarathonClient(m_adrs)
    try:
      return cli.get_app(app_name, True)
    except marathon.exceptions.MarathonError as e:
      print "Got: {0}".format(e)
      time.sleep(6)
  return None

def get_app_instances(marathon_addresses, app_name):
  tasks = _get_marathon_response(marathon_addresses, app_name)
  if tasks is None:
    return 0
  return int(tasks.instances)

# app_name = 'chronos'
# marathon_addresses = 'http://hadoop-ha-1:8773,http://hadoop-ha-2:8773'
def get_app_tasks(marathon_addresses, app_name):
  app = _get_marathon_response(marathon_addresses, app_name)
  app.tasks
  if app is None:
    return []
  tasks = [{'host':str(x.host), 'ip':socket.gethostbyname(str(x.host)), 'ports': x.ports, 'stagedAt': str(x.staged_at)} for x in app.tasks]
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
def get_addresses_by(tasks, attribute='host', prefix=''):
  adrs = [_get_joined(adr[attribute], adr['ports']) for adr in tasks]
  adrs = map(list, zip(*adrs))
  adrs = [str(','.join(a)) for a in adrs]
  return {"{2}_TASK_{1}_PORT{0}".format(j, attribute.upper(), prefix): adrs[j] for j in range(0,len(adrs))}


if __name__ == "__main__":
  pass
