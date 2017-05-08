#!/usr/bin/env bash

# Testing Multiple Python Versions with Tox
# https://ben.fogbutter.com/2016/02/20/testing-multiple-python-versions-on-circleci.html
python -m unittest discover --start-directory ./tests/unit/