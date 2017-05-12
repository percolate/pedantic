.. include:: ../README.rst

Compatibility
-------------

Pedantic supports Python 2.7, 3.3, 3.4, 3.5 and 3.6.1

Installation
------------

Install & run:
 - From the top directory: ``pip install -r requirements.txt``
 - ``./pedantic.py /path/to/schema.json --whitelist=/path/whitelist.json``

Pedantic is also available as a Docker image `here <https://hub.docker.com/r/julienfunk/pedantic>`__.


API
---

.. autosimple:: pedantic.validator_service.validator


Test
----

To execute Pedantic suite of unit tests after installation, from top directory run:

    ``python -m unittest discover --start-directory ./tests/``


License
=======

This library uses the MIT license. See `LICENSE.txt <../LICENSE.txt>`__ for
more details