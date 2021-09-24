#!/usr/bin/env bash

last_ver=$(git describe --tags --abbrev=0)
next_ver=$(grep "__version__" drf_spectacular/__init__.py | sed "s/__version__ = '\\(.*\\)'/\\1/g")

echo
echo "$next_ver ($(date "+%Y-%m-%d"))"
echo "-------------------"
echo

git log ${last_ver}..origin/master --pretty=format:"- %s [%an]" --no-merges  \
    | sed 's/\[T. Franzel\]//g' \
    | sed 's|\#\([0-9]\+\)|`#\1 <https://github.com/tfranzel/drf-spectacular/issues/\1>`_|g' \
    | sed 's/[ \t]*$//'

echo
