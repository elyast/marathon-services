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
      out = subprocess.check_output([self.command, '-p', str(self.port), 'replicate', master_id])
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

  def parse_entry(self, e):
    return {'id': e[0], 'address':e[1], 'type':e[2], 'slaveof':e[3]}

  # str_out = 'b4f549ee553acd1f07eaf2a0815340c2ce6cea38 127.0.0.1:7001 myself,master - 0 0 0 connected\n74eacbf979e0c057aa7975f044e02ac3d9ea069d 127.0.0.1:7002 master - 0 1413662635708 1 connected\n708abf8d79801549c53eab287658be62089df6cd 14.255.247.70:9055 slave e6293fc99b05a4761fa506c77d0e43d44a0b758e 0 1413396813263 6 connected\n'
  def parse_config(self, str_out):
    entries = [e.split() for e in str_out.split('\n') if len(e) > 0]
    entries = map(self.parse_entry, entries)

    myself = [e for e in entries if "myself" in e['type']]
    peers = [e for e in entries if "myself" not in e['type']]
    peer_masters = [e for e in entries if "myself" not in e['type'] and 'master' in e['type']]
    return {'myself': myself[0], 'peers': peers, 'peer_masters': peer_masters}

  def nodes_config(self):
    try:
      out = subprocess.check_output([self.command, '-p', str(self.port), 'cluster', 'nodes'])
      return (True, self.parse_config(out))
    except subprocess.CalledProcessError as e:
      print "ERR nodes config {0}".format(e.output)
      return (False, {})

  # masters = [{'slaveof': '-', 'type': 'master', 'id': '74eacbf979e0c057aa7975f044e02ac3d9ea069d', 'address': '127.0.0.1:7002'}]
  def add_slave(self, masters, myself):
    print "Adding slave as {0}".format(myself)
    my_master = random.choice(masters)
    self.wait(self.replicate, [my_master['id']])

  # myself = {'slaveof': '-', 'type': 'myself,master', 'id': 'b4f549ee553acd1f07eaf2a0815340c2ce6cea38', 'address': '127.0.0.1:7001'}
  # no_of_masters_needed = 3
  # masters = [{'slaveof': '-', 'type': 'master', 'id': '74eacbf979e0c057aa7975f044e02ac3d9ea069d', 'address': '127.0.0.1:7002'}]
  def add_master(self, masters, myself, no_of_masters_needed):
    print "Adding master as {0}".format(myself)
    my_id = myself['id']
    masters_id = [m['id'] for m in masters]
    masters_id.append(my_id)
    sorted_masters_id = sorted(masters_id)
    my_index = sorted_masters_id.index(my_id)
    counter_start = my_index * self.token_no
    while(counter_start < self.max_slot):
      self.apply_slots(my_id, masters, counter_start, min(counter_start + self.token_no, self.max_slot))
      counter_start += no_of_masters_needed * self.token_no

  # range_start = 56
  # range_end = 112
  def apply_slots(self, my_id, masters, range_start, range_end):
    print "Applying slot {0}-{1} to id {2}".format(range_start, range_end, my_id)
    for t in range(range_start, range_end):
      self.apply_slot(my_id, masters, t)

  def set_slot(self, my_id, masters, slot):
    try:
      cmd = [self.command, '-p', str(self.port), 'cluster', 'setslot', str(slot), 'node', my_id]
      out = subprocess.check_output(cmd)
      return (True, out)
    except subprocess.CalledProcessError as e:
      print "ERR set_slot {0}".format(e.output)
      return (False, None)

  def apply_slot(self, my_id, masters, slot):
    cli.wait(cli.set_slot, [my_id, masters, slot])

  def wait_for_config(self, no_of_current_nodes):
    for t in range(0, 300):
      success, out = cli.wait(cli.nodes_config)
      current_known_peers_no = len(out['peers'])
      if success and current_known_peers_no + 1 >= no_of_current_nodes:
        return (success, out)
      else:
        print "Conditions not met {0}, {1}".format(success, current_known_peers_no)
        time.sleep(1)

# seed_uri_conf_file = 'seed_uri_test.yml'
# redis_conf_file = 'redis-3.0.0-rc1/7001/redis.conf'
# my_port = 7001
if __name__ == "__main__":
  my_port = os.environ['PORT0']
  seed_uri_conf_file = sys.argv[1]
  with open(seed_uri_conf_file) as cf:
    config = yaml.load(cf)
  print "Running cluster reconfiguration"
  cli = RedisClient(my_port)
  success,out = cli.wait(cli.ping)
  if not success:
    print "Cannot connect to Redis:{0} check your config".format(my_port)
    sys.exit(1)
  print "Connected: {0}:{1}".format(success, out)
  seeds = config['seeds']
  no_of_masters_needed = len(seeds.split(','))
  no_of_current_nodes = config['current_task_no']

  all_meetings = cli.cluster_all_meet(seeds)
  all_succedded = reduce(operator.and_, [x[0] for x in all_meetings], True)
  if not all_succedded:
    print "Couldnt meet with some servers {0}".format(all_meetings)
    sys.exit(1)

  success,current_config = cli.wait_for_config(no_of_current_nodes)
  if not success:
    print "Cannot see enough nodes in config {0} currently {1}".format(no_of_current_nodes, current_config)
    sys.exit(1)
  print "Current seen config: {0}".format(current_config)
  if (len(current_config['peer_masters']) >= no_of_masters_needed):
    cli.add_slave(current_config['peer_masters'], current_config['myself'])
  else:
    cli.add_master(current_config['peer_masters'], current_config['myself'], no_of_masters_needed)
  print "End of configuring cluster"
