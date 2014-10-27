#!/usr/bin/env python

import os
import re
import sys
import time
import subprocess
import os
import yaml
import sys, time
import operator
import random
from collections import defaultdict
from operator import itemgetter

def parse_entry(e):
  return {'id': e[0], 'address':e[1], 'flags':e[2].split(','), 'slaveof':e[3],
          'ping_sent':e[4], 'ping_recv':e[5], 'config_epoch':e[6], 'link_status':e[7], 'slots':e[8:]}

# str_out = '3e3a6cb0d9a9a87168e266b0a0b24026c0aae3f0 127.0.0.1:7001 master - 0 1385482984082 0 connected 5960-10921\n2938205e12de373867bf38f1ca29d31d0ddb3e46 127.0.0.1:7002 master - 0 1385482983582 0 connected\n97a3a64667477371c4479320d683e4c8db5858b1 :0 myself,master - 0 0 0 connected 0-5959 10922-11422\n'
def parse_config(str_out):
  entries = [e.split() for e in str_out.split('\n') if len(e) > 0]
  return map(parse_entry, entries)

class RedisClient:
  def __init__(self, port):
    self.port = port
    self.command = "src/redis-cli"
    self.token_no = 56
    self.max_slot = 16384

  def ping(self):
    try:
      out = subprocess.check_output([self.command, '-p', str(self.port), 'ping'])
      return (True, out)
    except subprocess.CalledProcessError as e:
      print "ERR ping {0}".format(e.output)
      return (False, None)

  def cluster_meet(self, seed):
    try:
      ip, port = seed.split(':')
      out = subprocess.check_output([self.command, '-p', str(self.port), 'cluster', 'meet', ip, port])
      return (True, out)
    except subprocess.CalledProcessError as e:
      print "ERR cluster meet {0}".format(e.output)
      return (False, None)

  def replicate(self, master_id):
    try:
      out = subprocess.check_output([self.command, '-p', str(self.port), 'cluster', 'replicate', master_id])
      return (True, out)
    except subprocess.CalledProcessError as e:
      print "ERR replicate {0}".format(e.output)
      return (False, None)

  def cluster_all_meet(self, seeds):
    seed_ar = seeds.split(',')
    print "Seeds: {0}".format(seed_ar)
    results = []
    for seed in seed_ar:
      results.append(self.wait(self.cluster_meet, [seed]))
    return results

  def wait(self, command, args=()):
    for t in range(0, 10):
      success, out = command(*args)
      if success:
        return (success, out)
      else:
        print "Command: {0} with {1} failed, repeating {2}...".format(command, out, t)
        time.sleep(1)
    return (False, None)

  def nodes_config(self):
    try:
      out = subprocess.check_output([self.command, '-p', str(self.port), 'cluster', 'nodes'])
      return (True, parse_config(out))
    except subprocess.CalledProcessError as e:
      print "ERR nodes config {0}".format(e.output)
      return (False, {})

  # masters = [{'slaveof': '-', 'type': 'master', 'id': '74eacbf979e0c057aa7975f044e02ac3d9ea069d', 'address': '127.0.0.1:7002'}]
  def add_slave(self, predecesors, current_config):
    my_master = None
    for t in range(0, 30):
      masters = [x for x in current_config['predecesors'] if 'master' in x['flags'] and len(x['slots']) > 0]
      if len(masters) > 0:
        my_master = random.choice(masters)
        break
      else:
        success,current_config = cli.wait_for_config(predecesors)
        print "Cannot choose master from {0}".format(current_config)
        time.sleep(1)

    print "Adding slave as {0} for the guy {1}".format(current_config['myself'], my_master)
    self.wait(self.replicate, [my_master['id']])

  # myself = {'slaveof': '-', 'type': 'myself,master', 'id': 'b4f549ee553acd1f07eaf2a0815340c2ce6cea38', 'address': '127.0.0.1:7001'}
  # no_of_masters_needed = 3
  # masters = [{'slaveof': '-', 'type': 'master', 'id': '74eacbf979e0c057aa7975f044e02ac3d9ea069d', 'address': '127.0.0.1:7002'}]
  def add_master(self, no_of_masters_needed, current_config):
    myself = current_config['myself']
    print "Adding master as {0}".format(myself)
    my_id = myself['id']
    my_index =  myself['index']
    counter_start = my_index * self.token_no
    while(counter_start < self.max_slot):
      self.apply_slots(my_id, counter_start, min(counter_start + self.token_no, self.max_slot))
      counter_start += no_of_masters_needed * self.token_no

  # range_start = 56
  # range_end = 112
  def apply_slots(self, my_id, range_start, range_end):
    print "Applying slot {0}-{1} to id {2}".format(range_start, range_end, my_id)
    for t in range(range_start, range_end):
      self.apply_slot(my_id, t)

  def set_slot(self, my_id, slot):
    try:
      cmd = [self.command, '-p', str(self.port), 'cluster', 'setslot', str(slot), 'node', my_id]
      out = subprocess.check_output(cmd)
      return (True, out)
    except subprocess.CalledProcessError as e:
      print "ERR set_slot {0}".format(e.output)
      return (False, None)

  def apply_slot(self, my_id, slot):
    cli.wait(cli.set_slot, [my_id, slot])

  # all_nodes = '10.133.5.67:9031,10.133.5.50:32900,10.133.5.37:9131,10.133.5.67:33821,10.133.5.60:9390,10.133.5.37:9362,10.133.5.68:9201,10.133.5.47:9288,10.133.5.67:9015'
  # my_address = '10.133.5.67:33821'
  # my_address = '10.133.5.37:9131'
  # predecesors = find_my_predecesors(all_nodes, my_address)
  # out = parse_config('3e3a6cb0d9a9a87168e266b0a0b24026c0aae3f0 10.133.5.67:9031 master - 0 1385482984082 0 connected 5960-10921\n2938205e12de373867bf38f1ca29d31d0ddb3e46 10.133.5.50:32900 master - 0 1385482983582 0 connected\n97a3a64667477371c4479320d683e4c8db5858b1 10.133.5.37:9131 myself,master - 0 0 0 connected 0-5959 10922-11422\n')
  def wait_for_config(self, predecesors):
    for t in range(0, 300):
      success, out = cli.wait(cli.nodes_config)
      d = defaultdict(dict)
      for l in (predecesors, out):
          for elem in l:
              d[elem['address']].update(elem)
      joined_config = d.values()
      only_predecesors = [x for x in joined_config if 'index' in x]
      myself = [x for x in out if 'myself' in x['flags']][0]
      myself['index'] = len(predecesors)
      all_predecesors_covered = reduce(operator.and_, ['id' in x and 'link_status' in x and x['link_status'] == 'connected' for x in only_predecesors], True)
      if success and all_predecesors_covered:
        return (success, {'predecesors': only_predecesors, 'myself': myself})
      else:
        print "Conditions not met {0}, {1}".format(success, only_predecesors)
        time.sleep(1)

# all_nodes = '10.133.5.67:9031,10.133.5.50:32900,10.133.5.37:9131,10.133.5.67:33821,10.133.5.60:9390,10.133.5.37:9362,10.133.5.68:9201,10.133.5.47:9288,10.133.5.67:9015'
# my_address = '10.133.5.67:9031'
# my_address = '10.133.5.67:33821'
# my_address = '10.133.5.67:9015'
# my_address = '10:1'
def find_my_predecesors(all_nodes, my_address):
  nds = all_nodes.split(",")
  if my_address not in nds:
    return []
  j = nds.index(my_address)
  return [{'index': i, 'address': nds[i]} for i in range(0, len(nds)) if i < j]

def should_be_master(no_of_masters_needed, current_config):
  my_index = current_config['myself']['index']
  print 'My index {0}'.format(my_index)
  peers = current_config['predecesors']
  counter = 0
  for t in peers:
    print 'Checking peer {0}'.format(t)
    if t['index'] < my_index and 'master' in t['flags']:
      counter += 1
  print 'Current no of masters {0} vs needed {1}'.format(counter, no_of_masters_needed)
  return counter < no_of_masters_needed

# seed_uri_conf_file = 'seed_uri_test.yml'
# redis_conf_file = 'redis-3.0.0-rc1/7001/redis.conf'
# my_port = 7001
if __name__ == "__main__":
  seed_uri_conf_file = sys.argv[1]
  with open(seed_uri_conf_file) as cf:
    config = yaml.load(cf)
  my_address = config['my_address']
  my_ip, my_port = my_address.split(":")
  seeds = config['seeds']
  all_nodes = config['all']
  print "Running cluster reconfiguration me {0}, ".format(my_address)
  cli = RedisClient(my_port)
  success,out = cli.wait(cli.ping)
  if not success:
    print "Cannot connect to Redis:{0} check your config".format(my_port)
    sys.exit(1)
  print "Connected: {0}:{1}".format(success, out)
  no_of_masters_needed = len(seeds.split(','))

  all_meetings = cli.cluster_all_meet(seeds)
  all_succedded = reduce(operator.and_, [x[0] for x in all_meetings], True)
  if not all_succedded:
    print "Couldnt meet with some servers {0}".format(all_meetings)
    sys.exit(1)

  predecesors = find_my_predecesors(all_nodes, my_address)
  success,current_config = cli.wait_for_config(predecesors)
  print "Current seen config: {0}".format(current_config)
  if (should_be_master(no_of_masters_needed, current_config)):
    cli.add_master(no_of_masters_needed, current_config)
  else:
    cli.add_slave(predecesors, current_config)
  print "End of configuring cluster"
