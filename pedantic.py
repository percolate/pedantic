#!/usr/bin/env python
"""
Configure and start the Pedantic service.

Usage:
    pedantic.py SCHEMA_PATH [--whitelist=<whitelist_path>] [--port=<port_number>]

Example:
    pedantic.py /path/to/schema/file.json --whitelist=/path/whitelist.json

Options:
    -h, --help                      Show this screen and exit.
    --version                       Show version.
    --whitelist=<whitelist_path>    Path to file containing JSON whitelist contents.
    --port=<port_number>            Set the port number of the service, default `5000`.

"""

from docopt import docopt

import pedantic.validator_service as val


def runserver():
    with open(arguments['SCHEMA_PATH'], 'r') as f:
        schema = f.read()

    whitelist_path = arguments['--whitelist']
    if not whitelist_path:
        whitelist = None
    else:
        with open(whitelist_path, 'r') as f:
            whitelist = f.read()

    port = arguments['--port']
    if not port:
        port = 5000
    else:
        port = int(port)

    val.set_proxy_settings(schema, whitelist)
    val.app.run(port=port)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Pedantic 0.1')
    print(arguments)
    runserver()
