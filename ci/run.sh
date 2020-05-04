#!/bin/bash

set -eu
PIPELINE_NAME="docker-goesutils"

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
export fly_target=${fly_target:-hemna}
echo "Concourse API target ${fly_target}"
echo "Hemna $(basename $DIR)"

if [ ! -f credentials.yml ]; then
    echo "You need to create credentials.yml"
    exit 1
fi

pushd $DIR
  fly -t ${fly_target} set-pipeline -p $PIPELINE_NAME -c pipeline.yml -l credentials.yml
  fly -t ${fly_target} unpause-pipeline -p $PIPELINE_NAME
  fly -t ${fly_target} trigger-job -w -j $PIPELINE_NAME/build-and-publish-goesutils
popd
