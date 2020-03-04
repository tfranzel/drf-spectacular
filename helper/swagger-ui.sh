#!/usr/bin/env bash
if [ "$#" -ne "1" ] ; then
	echo usage: $0 SCHEMA
	exit 1
fi

SCHEMA=$1
SCHEMA_PATH=${PWD}/${SCHEMA}

docker pull swaggerapi/swagger-ui

echo
echo UI running at http://localhost:8088

docker run -p 8088:8080 -e SWAGGER_JSON=/schema.yml -v ${SCHEMA_PATH}:/schema.yml swaggerapi/swagger-ui
