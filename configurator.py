#!/usr/bin/python  

import urllib2
import json
import time
import os
import re
import sys

def file_replace(fname, patterns):
    # pattern is in the file, so perform replace operation.
    with open(fname) as f:
        out_fname = fname + ".tmp"
        out = open(out_fname, "w")
        for line in f:
			for i,j in patterns.iteritems():
   				line = line.replace("${0}".format(i),j)
   			out.write(line)
        out.close()
    os.rename(out_fname, fname)

def _get_url_opener():
    proxy_handler = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy_handler)
    opener.addheaders = [('Accept', 'application/json')]
    return opener

if __name__ == "__main__":
	marathon_host = os.environ['MARATHON_HOST']
	marathon_port = os.environ['MARATHON_PORT']	
	application = sys.argv[1]
	minimum_seeds = int(sys.argv[2])
	config_files = sys.argv[3].split(',')	
	seeds_requirement = True
	urler = _get_url_opener()
	marathon_url = "http://{0}:{1}/v2/apps/{2}".format(marathon_host, marathon_port, application)
	hosts = []
	while seeds_requirement:
		response = urler.open(marathon_url)
		apps = json.load(response)
		hosts = [x['host'] for x in apps['app']['tasks']] 
		seeds_requirement = len(hosts) < minimum_seeds
		if seeds_requirement:
			print "Seed requirement not met waiting 5 seconds..."
		else:
			print "Seed requirement met proceeding to launch..."
		time.sleep(5)
	patterns = {"MARATHON_SEED_NODES": str(','.join(hosts))}
	patterns.update(os.environ)
	for x in config_files:
		file_replace(x, patterns)
