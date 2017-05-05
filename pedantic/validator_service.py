"""Pedantic service providing REST API for fixture validation."""

from __future__ import absolute_import, unicode_literals
import json

from flask import Flask, request, jsonify

from check_against_schema import (
    validate_request_against_schema,
    validate_response_against_schema,
    is_whitelisted,
    get_spec,
    parse_data,
    JSONSchemaValidationError,
    UndefinedSchemaError,
)

app = Flask(__name__)

schema = None
whiltelist = None


def set_proxy_settings(schema_arg, whitelist_arg):
    global schema
    global whitelist

    schema = json.loads(schema_arg)
    if whitelist_arg:
        whitelist = json.loads(whitelist_arg)


@app.route('/', methods=['POST'])
def validator():
    """
    .. http:POST:: /

        Receives relevant fixture information as POST JSON data payload. The
        data is validated and the validation result is returned.

        **Example request**:

        .. code-block:: bash

            curl -X POST -i http://localhost:5000/ --data '{"method":
            "POST", "path_info": "/api/v5/test/", "request":
            {"x": "data"}}' -H "Content-Type: application/json"

        **Example response**:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json
            Content-Length: 66

            {
              "message": "All is well with the world (and your fixture)."
            }

        :return: On success 200 is returned, otherwise 400 with error detail.

    """
    if 'application/json' not in request.headers.get('Content-Type'):
        msg = 'Transport header `Content-Type` must be `application/json`.'
        error = {'error': msg}
        return jsonify(error), 400

    json = request.get_json()
    try:
        data = parse_data(json)
    except ValueError as e:
        msg = {'error': e.message, 'data': json}
        return jsonify(msg), 400

    # Get the specific schema under test
    try:
        spec = get_spec(data, schema)
    except UndefinedSchemaError as e:
        if whitelist:
            if is_whitelisted(data, whitelist):
                msg = 'Requested endpoint `{}` is whitelisted against ' \
                      'validation.'.format(data.path)
                value = {'warning': msg}
                return jsonify(value), 200
        msg = {'error': e.message}
        return jsonify(msg), 400

    # Validate the request and/or response
    errors = ''
    if data.request:
        try:
            validate_request_against_schema(data, spec)
        except JSONSchemaValidationError as e:
            errors = '{}\n\n'.format(e.message)

    if data.response:
        try:
            validate_response_against_schema(data, spec)
        except JSONSchemaValidationError as e:
            errors += e.message

    # Return the results
    if not errors:
        msg = {'message': 'All is well with the world (and your fixture).'}
        return jsonify(msg), 200
    else:
        msg = {'error': errors}
        return jsonify(msg), 400
