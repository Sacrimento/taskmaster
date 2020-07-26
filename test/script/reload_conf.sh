#!/bin/bash

echo "status"
cp "./test/yaml/starttime.yml" "/tmp/reload_conf.yml"
echo "start starttime"
echo "status"
echo "reread"
echo "status"
cp "./test/yaml/stoptime.yml" "/tmp/reload_conf.yml"
echo "start stoptime"
echo "status"
