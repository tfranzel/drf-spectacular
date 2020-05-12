#!/usr/bin/env bash
if [ $# -lt 2 ] ; then
	echo "usage: $0 SCHEMA TARGET [NAME]"
	exit 1
fi

SCHEMA=$1
SCHEMA_PATH=${PWD}/${SCHEMA}
TARGET=$2
OUTPUT_NAME=${3:-$TARGET}
OUTPUT_PATH=${PWD}/generated_clients/${OUTPUT_NAME}

mkdir -p $OUTPUT_PATH
echo "removing old client at ${OUTPUT_PATH}"
sudo rm -rf ${OUTPUT_PATH}

docker pull openapitools/openapi-generator-cli
echo "generator version: $(docker run --rm openapitools/openapi-generator-cli version)"

docker run --rm -v ${SCHEMA_PATH}:/schema.yml -v ${OUTPUT_PATH}:/build openapitools/openapi-generator-cli generate \
	-i /schema.yml \
	-g ${TARGET} \
	-o /build

sudo chown -R $USER:$USER $OUTPUT_PATH
cp ${SCHEMA_PATH} ${OUTPUT_PATH}/schema.yml
