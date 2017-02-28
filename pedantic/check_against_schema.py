from __future__ import unicode_literals
import json
import re
import os

from collections import namedtuple

from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator
from urlparse import parse_qs
from dateutil.parser import parse as validate_date

import logging
log = logging.getLogger(__name__)

Data = namedtuple('Data', 'path method request_data response_data query_data')


class JSONSchemaValidationError(Exception):
    """Raised for errors specific to schema validation"""


class UndefinedSchemaError(Exception):
    """
    Used to discover which APIs still require definitions. There are
    tasks to follow up with the eventual removal of this exemption.
    """
    pass


class ResponseNotDefinedError(Exception):
    """
    Used to discover which APIs still require definitions. There are
    tasks to follow up with the eventual removal of this exemption.
    """
    pass


def parse_data(json_data):
    """
    Parses the request parameter.

    :param dict json_data: the request json

    :rtype nametuple: Contains relevant information from the request object.
        str path: path info of the eg '/api/v5/post'
        str method: the method type of the request eg 'post', 'put' etc
        dict request_data: the data payload of the mock request
        dict response_data: the data payload of the mock response
        dict query_data: query string items
    """
    query_data = parse_qs(
        json_data['query_string'],
        keep_blank_values=True
    )
    for key in query_data:
        # everything from query string is in a list, even if single element
        if len(query_data[key]) == 1:
            # remove the enclosing list from non-list types
            query_data[key] = _parse_from_string(query_data[key][0])
        else:
            for idx, val in enumerate(query_data[key]):
                query_data[key][idx] = _parse_from_string(val)

    return Data(
            path=json_data['path_info'],
            method=json_data['request_method'],
            request_data=json_data['request'],
            response_data=json_data['response'],
            query_data=query_data
    )


def get_hotlanta_schema(schema_file):
    """
    Returns the definition of all Percolate schemas from the specification

    :param string: allows injection of alternative schemas (usually for test)

    :rtype dict:
    """
    # Read the file when it is needed rather than at module load time
    global JSONSCHEMA_API
    if JSONSCHEMA_API is None:
        filename = os.path.join(schema_file)
        with open(filename, 'r') as f:
            read_data = f.read()
        JSONSCHEMA_API = json.loads(read_data)
    return JSONSCHEMA_API


def is_whitelisted(info, whitelist):
    if hasattr(info, 'request'):
        path = info.request['path_info']
        method = info.request['request_method']
        code = info.status_code
    else:
        path = info['path_info']
        method = info['request_method']
        code = None

    for item in whitelist:
        match = re.match(item['path'], path)
        if match:
            if 'code' in item:
                if code:
                    # if whitelist code exists it should also have the method
                    if item['code'] == code and item['method'] == method:
                        return True
            elif 'method' in item and method:
                if item['method'] == method:
                    return True
            else:
                return True


def _get_path_segments(path_info):
    # split the path into segments starting w '/'
    # eg ['/api', '/v5', '/post', '/']
    path_segment_list = re.findall(r'\/[^\/]*', path_info)

    paths = {
        'remaining': path_segment_list,
        'path_info': path_info,
    }
    return paths


def _get_method_spec_from_resource(endpoint, request):
    req_method = request.method.lower()
    for method in endpoint['methods']:
        if method['method'].lower() == req_method:
            return method
    raise UndefinedSchemaError(
        "The requested method '{}' for '{}' was not found in spec.".format(
            req_method, request.path))


uri_param_key = re.compile(r'{(.*)}')


def _match_uri_segments(req_segments, relative_segs, rsrc):
    for idx, (rel_seg, seg) in enumerate(zip(relative_segs, req_segments)):
        if rel_seg != seg:
            key = uri_param_key.search(rel_seg)
            if key:
                schema = rsrc['uriParameters'][key.group(1)]
                err_msg = _do_param_validation(seg.lstrip('/'), schema)
                if err_msg:
                    return False  # don't raise, there may be other resources
            else:
                return False
    return req_segments[len(relative_segs):]


segments = re.compile(r'\/[^\/]*')


def _find_resource(schemas, paths):
    """ Recursively walks the schema to find the matching resource """
    req_segs = paths['remaining']
    if 'resources' in schemas:
        for rsrc in schemas['resources']:
            relative_segs = segments.findall(rsrc['relativeUri'])
            if len(req_segs) >= len(relative_segs):
                remaining_segs = _match_uri_segments(req_segs,
                                                     relative_segs, rsrc)
                if remaining_segs:
                    paths['remaining'] = remaining_segs
                    return _find_resource(rsrc, paths)
                elif type(remaining_segs) == list:
                    return rsrc
    raise UndefinedSchemaError(
        "The requested resource '{}' was not found in spec.".format(
            paths['path_info']))


def get_spec(request, schemas):
    """
    Returns the schema definition for the data instance in the request

    :param namedtuple request: generated by `parse_data`

    :param dict schemas: the global specification containing all schemas

    :rtype dict: the matched method's jsonschema definition
    """
    paths = _get_path_segments(request.path)
    resource = _find_resource(schemas, paths)
    return _get_method_spec_from_resource(resource, request)


def _parse_from_string(a_string):
    try:
        field = json.loads(a_string)
    except Exception:
        field = a_string

    # if the field has a comma, may be a list
    if isinstance(field, basestring) and ',' in field:
        field = [_parse_from_string(item) for item in field.split(",")]
    return field


def _do_param_validation(param, schema):
    err_msg = ""
    if isinstance(param, dict):
        param = json.dumps(param)
    # if the parameter is a list, validate each element against the schema
    elif isinstance(param, list):
        for item in param:
            err_msg = "".join(
                [err_msg, _do_param_validation(item, schema)]
            )
        return err_msg
    # sometimes a number should be a string
    elif isinstance(param, (int, long, float)) and schema['type'] == 'string':
        param = unicode(param)

    if schema['type'] == 'date':
        try:
            validate_date(param)
        except ValueError as e:
            if "Unknown string format" in e.message:
                err_msg = (" - Request query param '{}' does not conform"
                           " to any known date format.\n".format(param))
            else:
                raise e
        return err_msg

    try:
        _validate(param, schema)
    except Exception as e:
        err_msg = e.message
    return err_msg


def _get_pretty_path(col_dq):
    path_string = ""
    for path_item in col_dq:
        if isinstance(path_item, int):
            path_string = "".join([path_string, "[", str(path_item), "]"])
        else:
            path_string = "".join([path_string, ".", path_item])
    return path_string


def _validate(data, schema):
    # custom validation for clean and comprehensive error output
    err_msg = ""
    validator = Draft4Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda x: x.path)
    for error in errors:
        err_msg = "".join([err_msg, " - ",
                           _get_pretty_path(error.absolute_path),
                           ": ", error.message, "\n"])
        suberrors = sorted(error.context, key=lambda e: e.schema_path)
        for suberror in suberrors:
            err_msg = ("".join([
                err_msg, "     > Schema path: ",
                unicode(list(suberror.schema_path)),
                " Error: ", suberror.message, "\n"
            ]))
    if errors:
        raise ValidationError(err_msg)


def validate_request_against_schema(req_info, spec):
    """
    Validates the query parameters and body data of a test client request.

    :param dict req_info: the instance data of the request

    :param dict spec: the relevant jsonschema definition for the instance

    :rtype None

    :raises: :class:
        `.JSONSchemaValidationError`
    """
    req_data = req_info.request_data
    req_params = req_info.query_data
    err_msg = ""

    # `api_key` is not in spec, it is being deprecated, however,
    # it is present in most requests so we remove it here to allow
    # `additionalProperties: false`
    if 'api_key' in req_params:
        del req_params['api_key']

    # validate query parameters
    if req_params and 'queryParameters' in spec:

        for key in spec['queryParameters']:
            if 'required' in spec['queryParameters'][key]:
                # We delete RAML's `required` field otherwise it won't
                # validate using JSONSchema
                del spec['queryParameters'][key]['required']
                qp_schema = spec['queryParameters'][key]
                # validate required fields in place since they're ready
                try:
                    err_msg = "".join([
                        err_msg,
                        _do_param_validation(req_params[key], qp_schema)
                    ])
                except KeyError as e:
                    err_msg = "".join([
                        err_msg,
                        " - Missing required query param: '", key, "'\n"
                    ])
                else:
                    # delete the field so it is not validated twice
                    del req_params[key]
        for param in req_params:
            try:
                qp_schema = spec['queryParameters'][param]
            except KeyError as e:
                err_msg = "".join([err_msg, " - Query parameter '", e.message,
                                   "' undefined in specification.\n"])
            else:
                err_msg = "".join([
                    err_msg,
                    _do_param_validation(req_params[param], qp_schema)
                ])
    elif req_params:
        err_msg = " - `queryParameters` must be defined in specification\n"

    if err_msg:
        err_msg = "".join([
            "\n\nRequest query param validation errors...\n\n", err_msg])

    # validate request body
    if req_data and 'body' in spec:
        # `api_key` is not in spec, it is being deprecated, however,
        # it is present in most requests so we remove it here to allow
        # `additionalProperties: false`
        if 'api_key' in req_data:
            del req_data['api_key']

        raw_instance_sch = spec['body']['application/json']['schema']
        instance_schema = json.loads(raw_instance_sch)
        try:
            _validate(req_data, instance_schema)
        except Exception as e:
            err_msg = "".join([
                err_msg, "\nRequest data validation errors...\n\n",
                e.message])

    # Finally raise all validation errors at once
    if err_msg:
        err_msg = "".join([
            err_msg, "\nRequest detail:\n\n'",
            unicode(json.loads(json.dumps(req_info))), "\n"])
        raise JSONSchemaValidationError(err_msg)


def validate_response_against_schema(response, spec):
    """
    Validates the instance data from the response.

    :param response: the response object returned by the request
    :type response: rest_framework.response.Response or
        django.http.response.HttpResponse

    :param dict spec: the relevant jsonschema definition for the instance

    :raises: :class:`.ResponseNotDefinedError`
    """
    res_status_code = unicode(response.status_code)
    # Now match the response status code with the schema for the code
    for code, value in spec['responses'].iteritems():
        if code == res_status_code:
            if 'body' in value:
                json_response = value['body']['application/json']
                if not json_response:
                    return
                raw_instance_schema = (
                    json_response['schema'])
                instance_schema = json.loads(raw_instance_schema)
                data = json.loads(response.content)
                try:
                    _validate(data, instance_schema)
                except Exception as e:
                    msg = "".join([
                        "Found during response validation:\n",
                        e.message,
                        "\nRequest detail:\n\n'", unicode(response.request),
                        "\n\nResponse detail:\n\n",
                        "STATUS CODE: ", unicode(response.status_code),
                        "\nCONTENT: ",
                        unicode(json.loads(json.dumps(response.content))),
                        "\n"])
                    raise JSONSchemaValidationError(msg)
                return
            else:
                return
    raise ResponseNotDefinedError(
        "The status code '{}' for method '{}' and path '{}' is not defined by"
        " the specification.".format(
            res_status_code,
            unicode(response.request['request_method']),
            unicode(response.request['path_info'])
        )
    )
