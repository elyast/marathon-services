#!/bin/bash -x

# Our elasticsearch-mesos project version follows the Elasticsearch version number
ESVERSION=1.3.4

echo Building Elasticsearch $ESVERSION for Mesos

rm -r elasticsearch-mesos-*
curl https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-${ESVERSION}.tar.gz -o elasticsearch-${ESVERSION}.tar.gz

tar xzf elasticsearch-*.tar.gz
rm elasticsearch-*tar.gz

mv elasticsearch-${ESVERSION} elasticsearch-mesos-${ESVERSION}

cp ../configurator.py elasticsearch-mesos-${ESVERSION}/
chmod u+x elasticsearch-mesos-${ESVERSION}/configurator.py

cp config/* elasticsearch-mesos-${ESVERSION}/config

tar czf elasticsearch-mesos-${ESVERSION}.tgz elasticsearch-mesos-${ESVERSION}
