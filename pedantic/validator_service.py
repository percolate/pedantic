"""Some placeholder module text"""

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
    .. http:GET:: /

        Placeholder route doctext.

        **Example request**:

        .. code-block:: bash

            curl -i http://localhost:5000/ -d <TODO DATA HERE>

        :return: The response returned to the proxy.

    """


    # params = dict(request.args)
    # print('X: {}'.format(json['x']))
    # print("Params: {}".format(params))
    # print("Data: {}".format(request.data))
    # print("Files: {}".format(request.files))
    # print("Headers: {}".format(request.headers))
    # print("Form: {}".format(request.form))
    # print("Cookies: {}".format(request.cookies))
    # print("Stream: {}".format(request.stream.getvalue()))
    # print("JSON: {}".format(json))

    if 'application/json' not in request.headers.get('Content-Type'):
        msg = 'Transport header `Content-Type` must be `application/json`.'
        error = {'message': msg}
        return jsonify(error), 400

    json = request.get_json()
    try:
        data = parse_data(json)
    except ValueError as e:
        msg = {'message': e.message, 'data': json}
        return jsonify(msg), 400

    # Get the specific schema under test
    try:
        spec = get_spec(data, schema)
    except UndefinedSchemaError as e:
        if whitelist:
            if is_whitelisted(data, whitelist):
                msg = 'Requested endpoint is whitelisted against validation.'
                value = {'message': msg}
                return jsonify(value), 200
        msg = {'message': e.message}
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
        msg = {'message': errors}
        return msg, 400
