# prclt/pedantic

[![codecov](https://codecov.io/gh/percolate/pedantic/branch/master/graph/badge.svg)](https://codecov.io/gh/percolate/pedantic)

Pedantic allows any client to discover when a fixture no longer complies with a published API.

## Who is Pedantic for?

Pedantic is for client maintainers (front end, mobile etc..) who wish to automatically maintain test fixtures against services with an API specification defined in **RAML 0.8**.

### Rationale

Assuming the client developers write automated tests, it is best that client tests do not make external HTTP requests during the test process since that can lead to non-deterministic test results.
HTTP calls during testing are often avoided by creating mock requests in json.
While mock fixtures prevent external calls during testing, they do not prevent or detect a service provider's API changes.
When the API changes, tests which use outdated mocks continue to pass even though the actual client may no longer functions correctly.

Pedantic is a lightweight service designed to run on the same host as the test client and is accessible via `localhost`.
Provide Pedantic with the API definition in RAML, then during testing send the fixture data to Pedantic.
Pedantic validates the fixture and sends its results back to the caller.

## Usage

Display CLI help

```bash
docker run prclt/pedantic -h
```

Basic example caching (RAML/whitelist downloads) by mounting `:/tmp` as a volume:

```bash
docker run --rm --publish 5000:5000 --volume $(pwd)/tmp:/tmp prclt/pedantic https://percolate.com/docs/api/index.raml
```

```bash
curl -X POST -i http://localhost:5000/ --data '{
    "method": "PUT",
    "path_info": "/api/v5/user/user:1",
    "query_string": "required_param=a_string,optional_param=1",
    "status_code": 200,
    "request": {"name": "John Smith"},
    "response": {"data": {"name": "John Smith"}}
}' -H "Content-Type: application/json"
```

## Development

Build image locally

```bash
make build
```

Shell into `prclt/pedantic` with the repo mounted for development:

```bash
make dev

# from there you can run tests:
bin/test
bin/smoke_test
```
