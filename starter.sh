#!/bin/bash

if (type python3 2> /dev/null | grep -q is)
then PY_CMD=python3
elif (type python 2> /dev/null | grep -q is)
then PY_CMD=python
else
  echo 'Python is absent'
  exit
fi
MODULE_NAME=surgery_of_1c_storage
export PYTHONPATH=lib_linux

$PY_CMD $MODULE_NAME $*
