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

.. autoflask:: pedantic.validator_service:app
  :undoc-static:

.. code-block:: json

    {
        "title": "Pedantic POST API",
        "type": "object",
        "properties": {
            "path_info": {
                "description": "Path to the mocked resource.",
                "example": "/some/endpoint/",
                "type": "string"
            },
            "method": {
                "description": "Method of mocked request.",
                "example": "GET",
                "type": "string"
            },
            "request": "Documentation in progress",
            "response": "Documentation in progress",
            "query_string": {
                "description": "Mock request query string.",
                "example": "GET",
                "type": "string"
            },
            "status_code": "Documentation in progress"
        },
        "required": ["path_info", "method"],
        "oneOf" : [
            {
                "required" : ["request"]
            },
            {
                "required" : ["response"]
            }
        ]
    }

Test
----

To execute Pedantic suite of unit tests after installation, from top directory run:

    ``python -m unittest discover --start-directory ./tests/``


License
=======

This library uses the MIT license. See `LICENSE.txt <../LICENSE.txt>`__ for
more details