"""Some placeholder module text"""

from flask import Flask, request, jsonify

from pedantic.check_against_schema import (
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

    schema = schema_arg
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

    json = request.get_json()
    data = parse_data(json)

    try:
        spec = get_spec(data, schema)
    except UndefinedSchemaError as e:
        if is_whitelisted(data, whitelist):
            msg = 'Requested endpoint is whitelisted against validation.'
            return msg, 200
        else:
            return e.message, 400

    try:
        validate_request_against_schema(data.request, spec)
    except JSONSchemaValidationError as e:
        return e.message, 400

    try:
        validate_response_against_schema(data.response, spec)
    except JSONSchemaValidationError as e:
        return e.message, 400

    return 'All is well.', 200
