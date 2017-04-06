#!/usr/bin/env bash

set -ex

if [ ! -f "bin/activate" ]; then
  virtualenv .
fi

. ./bin/activate
pip install -r requirements.txt

cd pedantic
npm install
curl http://cdn.percolate.com.s3.amazonaws.com/index.raml > index.raml
curl http://cdn.percolate.com.s3.amazonaws.com/whitelist.json > whitelist.json
node convertRAML.js
