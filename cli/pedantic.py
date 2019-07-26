#!/usr/bin/env python
"""
Configure and start the Pedantic service.

Usage:
    pedantic <raml_url> [options]

Example:
    pedantic https://example.com/index.raml --whitelist=https://example.com/whitelist.json

Options:
    -h, --help          Show this screen
    --whitelist=URL     URL containing JSON whitelist contents
"""

from __future__ import absolute_import

import hashlib
import os
import subprocess
import tempfile
import time
from time import time

import docopt
import pedantic.validator_service as val


DEFAULT_TTL = 1800  # in seconds


def pedantic(args):
    tmp_dir = tempfile.gettempdir()
    raml_url = args["<raml_url>"]
    raml_url_hash = hashlib.md5(raml_url.encode("utf-8")).hexdigest()
    schema_path = os.path.join(tmp_dir, f"{raml_url_hash}.json")

    if (
        os.path.isfile(schema_path)
        and os.path.getmtime(schema_path) >= time() - DEFAULT_TTL
    ):
        log(f"RAML: cache found {schema_path}")
    else:
        # raml-parser must download the spec so it can resolve remote imports
        log(f"RAML: fetching/parsing {raml_url}...")
        subprocess.run(
            f"node cli/raml_parser.js {raml_url} {schema_path}", check=True, shell=True
        )

    with open(schema_path) as f:
        schema = f.read()

    whitelist = None
    if args["--whitelist"]:
        whitelist_url_hash = hashlib.md5(
            args["--whitelist"].encode("utf-8")
        ).hexdigest()
        whitelist_path = os.path.join(tmp_dir, f"{whitelist_url_hash}.json")
        download_to(args["--whitelist"], whitelist_path)
        with open(whitelist_path) as f:
            whitelist = f.read()

    val.set_proxy_settings(schema, whitelist)
    val.app.run(host="0.0.0.0", port=int(os.environ.get("PORT")))


def download_to(url, dest):
    log(f"Downloading ${url}...")
    cmd = f"curl --output {dest} --fail --retry 3 --progress-bar {url}"
    if os.path.isfile(dest):
        cmd += f" --time-cond {dest}"
    subprocess.run(cmd, check=True, shell=True)


def log(message):
    print(message, flush=True)


if __name__ == "__main__":
    pedantic(docopt.docopt(__doc__))
