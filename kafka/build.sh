#!/bin/bash -x

# Our elasticsearch-mesos project version follows the Elasticsearch version number
KAFKAVERSION=0.8.1.1
SCALA_VERSION=2.9.2
SUFFIX=_4

echo Building Kafka_${SCALA_VERSION} $KAFKAVERSION for Mesos

rm -r kafka-mesos-*
wget http://apache.osuosl.org/kafka/${KAFKAVERSION}/kafka_${SCALA_VERSION}-${KAFKAVERSION}.tgz

tar xzf kafka_${SCALA_VERSION}-${KAFKAVERSION}.tgz
rm kafka_${SCALA_VERSION}-${KAFKAVERSION}.tgz

mv kafka_${SCALA_VERSION}-${KAFKAVERSION} kafka-mesos_${SCALA_VERSION}-${KAFKAVERSION}${SUFFIX}

cp ../configurator.py kafka-mesos_${SCALA_VERSION}-${KAFKAVERSION}${SUFFIX}/
chmod u+x kafka-mesos_${SCALA_VERSION}-${KAFKAVERSION}${SUFFIX}/configurator.py

cp config/* kafka-mesos_${SCALA_VERSION}-${KAFKAVERSION}${SUFFIX}/config

tar czf kafka-mesos_${SCALA_VERSION}-${KAFKAVERSION}${SUFFIX}.tgz kafka-mesos_${SCALA_VERSION}-${KAFKAVERSION}${SUFFIX}
