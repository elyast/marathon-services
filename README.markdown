## Overview
This project allows you to utilize your Mesos cluster to run services like Cassandra, ElasticSearch, Kafka or Redis. 
Each directory contains sample json file that needs to be posted to marathon instance.

### Steps

First run build.sh in corresponding component, then make it available to Marathon/Mesos through HTTP / S3 / HDFS.
Secondly post json file, with your component URI, please note configuration templates are being processed using Marathon's env config.

## Known Limitations

Currently Mesos / Marathon doesn't offer support for stateful services, the only hope now is to run such service on every host
