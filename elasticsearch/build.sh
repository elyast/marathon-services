#!/bin/bash -x

# Our elasticsearch-mesos project version follows the Elasticsearch version number
ESVERSION=1.4.0
SUFFIX=_11

echo Building Elasticsearch $ESVERSION for Mesos

rm -r elasticsearch-mesos-*
curl https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-${ESVERSION}.tar.gz -o elasticsearch-${ESVERSION}.tar.gz

tar xzf elasticsearch-*.tar.gz
rm elasticsearch-*tar.gz

mv elasticsearch-${ESVERSION} elasticsearch-mesos-${ESVERSION}${SUFFIX}

cp -R ../launcher elasticsearch-mesos-${ESVERSION}${SUFFIX}/
chmod -R u+x elasticsearch-mesos-${ESVERSION}${SUFFIX}/launcher

cp config/* elasticsearch-mesos-${ESVERSION}${SUFFIX}/config

tar czf elasticsearch-mesos-${ESVERSION}${SUFFIX}.tgz elasticsearch-mesos-${ESVERSION}${SUFFIX}
