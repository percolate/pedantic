.. image:: https://codecov.io/github/j-funk/pedantic/coverage.svg?branch=master
   :target: https://codecov.io/github/j-funk/pedantic?branch=master
   :alt: Build Status
   :align: right

.. image:: https://circleci.com/gh/j-funk/pedantic.svg?style=shield&circle-token=02115294d1f76a7343f3df1cfd3d9c279a40969f
   :target: https://circleci.com/gh/j-funk/pedantic
   :alt: Code Coverage
   :align: right

########
Pedantic
########

Pedantic allows any client to discover when a fixture no longer complies with a published API.

Source code:
  https://github.com/j-funk/pedantic

Documentation:
  https://pedantic.readthedocs.io/

**Who is Pedantic for?**

Pedantic is for client maintainers (front end, mobile etc..) who wish to automatically maintain test fixtures against
services with an API specification defined in RAML 0.8.

**Rationale**

Assuming the client developers write automated tests, it is best that client tests do not make
external HTTP requests during the test process since that can lead to non-deterministic test results.  HTTP
calls during testing are often avoided by creating mock requests in json.  While mock fixtures will
prevent external calls during testing, they will not prevent or detect a service provider's API changes.
When the API changes, tests which use outdated mocks will continue to pass even though the actual client may no
longer function correctly.

Pedantic is a lightweight service designed to run on the same host as the test client and is accessible via
`localhost`.  Provide Pedantic with the API definition in RAML, then during testing send the fixture data
to Pedantic.  Pedantic validates the fixture and sends it's results back to the caller.
