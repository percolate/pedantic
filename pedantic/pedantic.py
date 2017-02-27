#!/usr/bin/env python
"""
Usage:
    pedantic.py SCHEMA_PATH [--whitelist=<path_to_whitelist>] [--port=<port_number>]

Example:
    pedantic path/to/schema/file.json


Arguments:
    service_name                    Used to organize contracts, creates a directory.
    destination_url                 The target for proxy forwarding while recording.
    contract_name                   The contract file name will be `<contract_name>.yaml`

Options:
    -h, --help                      Show this screen and exit.
    --version                       Show version.
    --port=<port_number>            Set the port number of the proxy, default `5000`.

"""

from docopt import docopt

import validator_service as val


def runserver():
    port = arguments['--port']
    if not port:
        port = 5000
    else:
        port = int(port)

    val.app.run(port=port)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Pedantic 0.1')
    print(arguments)
    runserver()
