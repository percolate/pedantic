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
    whitelist = whitelist_arg


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
        msg = 'Transport header `Content-Type` must be `application/json`. ' \
              'This is not a validation error.'
        return msg, 400

    json = request.get_json()

    # Ensure we have everything we need to before parsing
    required = ['path_info', 'request_method']
    if not all(item in json for item in required):
        msg = 'Data must contain the following fields: {}'.format(required)
        return msg, 400

    optional = ['query_string', 'request', 'response']
    for item in optional:
        if item not in json:
            json[item] = None

    data = parse_data(json)

    # Get the specific schema under test
    try:
        spec = get_spec(data, schema)
    except UndefinedSchemaError as e:
        if whitelist:
            if is_whitelisted(data, whitelist):
                msg = 'Requested endpoint is whitelisted against validation.'
                return msg, 200
        return e.message, 400

    # Validate the request and/or response
    errors = ''
    if json['request']:
        try:
            validate_request_against_schema(data, spec)
        except JSONSchemaValidationError as e:
            errors = '{}\n\n'.format(e.message)

    if json['response']:
        try:
            validate_response_against_schema(data, spec)
        except JSONSchemaValidationError as e:
            errors += e.message

    # Return the results
    if not errors:
        return 'All is well.', 200
    else:
        return errors, 400
