#!/bin/bash -v

# Our cassandra-mesos project version follows the Cassandra version number
CASSVERSION=2.1.0

echo Building Cassandra $CASSVERSION for Mesos

rm -r cassandra-mesos-*
wget http://apache.osuosl.org/cassandra/${CASSVERSION}/apache-cassandra-${CASSVERSION}-bin.tar.gz

tar xzf apache-cassandra*.tar.gz
rm apache-cassandra*tar.gz

mv apache-cassandra* cassandra-mesos-${CASSVERSION}

cp ../configurator.py cassandra-mesos-${CASSVERSION}/
chmod u+x cassandra-mesos-${CASSVERSION}/configurator.py

cp conf/* cassandra-mesos-${CASSVERSION}/conf

tar czf cassandra-mesos-${CASSVERSION}.tgz cassandra-mesos-${CASSVERSION}
