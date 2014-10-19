#!/bin/bash -x

# Our redis-mesos project version follows the redis version number
REDISVERSION=3.0.0-rc1
SUFFIX=_3

echo Building Redis $REDISVERSION for Mesos

rm -r redis-mesos-*
curl https://dl.dropboxusercontent.com/u/16106115/ubuntu/redis-${REDISVERSION}.tgz -o redis-${REDISVERSION}.tgz

tar xzf redis-*.tgz
rm redis-*tgz

mv redis-${REDISVERSION} redis-mesos-${REDISVERSION}${SUFFIX}

cp -R ../launcher redis-mesos-${REDISVERSION}${SUFFIX}/
cp launcher.py redis-mesos-${REDISVERSION}${SUFFIX}/launcher
chmod -R u+x redis-mesos-${REDISVERSION}${SUFFIX}/launcher

cp redis.conf redis-mesos-${REDISVERSION}${SUFFIX}/
cp seed_uri.yml redis-mesos-${REDISVERSION}${SUFFIX}/

tar czf redis-mesos-${REDISVERSION}${SUFFIX}.tgz redis-mesos-${REDISVERSION}${SUFFIX}
