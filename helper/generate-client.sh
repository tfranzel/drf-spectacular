#!/usr/bin/env bash
if [ "$#" -ne "2" ] ; then
	echo usage: $0 SCHEMA TARGET
	exit 1
fi

SCHEMA=$1
SCHEMA_PATH=${PWD}/${SCHEMA}
TARGET=$2
TARGET_PATH=${PWD}/generated_clients/$TARGET

echo removing old client at ${TARGET_PATH}
sudo rm -rf ${TARGET_PATH}

docker pull openapitools/openapi-generator-cli
docker run --rm -v ${SCHEMA_PATH}:/schema.yml -v ${TARGET_PATH}:/build openapitools/openapi-generator-cli generate \
	-i /schema.yml \
	-g ${TARGET} \
	-o /build
