#!/usr/bin/env bash

for file1 in test.py test_tools.py
do
  echo "[test] $file1"
  python tests/$file1
done

rm -rf build dist textmulclassify.egg-info # clean tmp files
