# coding: utf-8

import unittest
from copy import deepcopy
import json
import os
import sys
from collections import namedtuple

from pedantic.check_against_schema import (
    Data,
    is_whitelisted,
    _find_resource,
    _get_path_segments,
    validate_request_against_schema,
    validate_response_against_schema,
    parse_data,
    get_spec,
    JSONSchemaValidationError,
    UndefinedSchemaError,
    ResponseNotDefinedError,
)


schema_file = 'test_schemas_fixture.json'
with open(os.path.join(sys.path[0], schema_file), 'r') as f:
    read_data = f.read()
SCHEMAS = json.loads(read_data)


# Dummy object class for fixtures, using global makes tests 10x faster
class Object(object):
    def __getitem__(self, key):
        return getattr(self, key)


class ValidatorTestBase(unittest.TestCase):

    def setUp(self):
        self.raw_schema = deepcopy(SCHEMAS)
        self.req_path_info = '/api/v5/test/'
        self.method = 'post'
        self.data = {'request': {'x': 'data'}, 'response': {}}
        self.query_data = {'required_param': 'a string', 'optional_param': 1}
        self.parsed_data = Data(
            path=self.req_path_info,
            method=self.method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data=self.query_data
        )
        self.spec = get_spec(self.parsed_data, self.raw_schema)


class RequestValidatorTestCase(ValidatorTestBase):

    def test_validate_request_against_schema_quiet_on_valid_instance(self):
        """
        validate_request_against_schema() quietly completes on valid instance
        """
        # check ValidationError is not thrown
        validate_request_against_schema(self.parsed_data, self.spec)

    def test_validate_request_against_schema_quiet_on_valid_list_param(self):
        """
        validate_request_against_schema() quiet on valid list param instance
        """
        # check ValidationError is not thrown
        query_data = {
            'required_param': 'a string',
            'optional_param': [1, 2, 3, 4, 5]
        }
        req_info = Data(
            path=self.req_path_info,
            method=self.method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data=query_data
        )
        validate_request_against_schema(req_info, self.spec)

    def test_validate_request_against_schema_numbers_fallback_to_string(self):
        """
        validate_request_against_schema() quiet on valid list param instance
        """
        # check ValidationError is not thrown
        query_data = {
            'required_param': 1,
        }
        req_info = Data(
            path=self.req_path_info,
            method=self.method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data=query_data
        )
        validate_request_against_schema(req_info, self.spec)

    def test_validate_request_against_schema_many_errors_has_nice_output(self):
        """
        validate_request_against_schema() raises multiple types of (sub)errors
        """
        query_data = {
            'optional_param': 'not a number',
            'date_param': 'not a date',
            'not_defined_param': 'dummy'
        }
        req_info = Data(
            path=self.req_path_info,
            method=self.method,
            request_data={'x': 1, 'y': [{}, 3, "foo"]},
            response_data=self.data['response'],
            query_data=query_data
        )
        error_indicator = '-'
        suberror_indicator = '>'  # for sub schema errors
        stage_indicator = '...'   # once each for query and data validation

        try:
            validate_request_against_schema(req_info, self.spec)
        except JSONSchemaValidationError as e:
            self.assertGreater(e.message.count(error_indicator), 1)
            self.assertGreater(e.message.count(suberror_indicator), 1)
            self.assertGreater(e.message.count(stage_indicator), 1)
        else:
            self.fail("Did not raise JSONSchemaValidationError.")

    def test_validate_request_against_schema_invalid_date_list_param(self):
        """
        validate_request_against_schema() raises on invalid date list param
        """
        # check ValidationError is not thrown
        query_data = {
            'required_param': 'a string',
            'date_param': [
                '2016-06-14T13:58:32+00:00',
                'nonsense'
            ]
        }
        req_info = Data(
            path=self.req_path_info,
            method=self.method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data=query_data
        )
        with self.assertRaises(JSONSchemaValidationError):
            validate_request_against_schema(req_info, self.spec)

    def test_validate_request_against_schema_raises_with_invalid_data(self):
        """
        validate_request_against_schema() JSONSchemaValidationError on bad data
        """
        req_info = Data(
            path=self.req_path_info,
            method=self.method,
            request_data={'x': 1},
            response_data=self.data['response'],
            query_data=self.query_data
        )
        with self.assertRaises(JSONSchemaValidationError):
            validate_request_against_schema(req_info, self.spec)

    def test_validate_request_against_schema_missing_required_query(self):
        """
        validate_request_against_schema() raise on missing required query param
        """
        req_info = Data(
            path=self.req_path_info,
            method=self.method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data={'optional_param': 1}
        )
        with self.assertRaises(JSONSchemaValidationError):
            validate_request_against_schema(req_info, self.spec)

    def test_validate_request_against_schema_undefined_param(self):
        """
        validate_request_against_schema() raises for undefined schema field
        """
        req_info = Data(
            path=self.req_path_info,
            method=self.method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data={'required_param': "dummy", 'not_defined': "dummy"}
        )
        with self.assertRaises(JSONSchemaValidationError):
            validate_request_against_schema(req_info, self.spec)

    def test_validate_request_against_schema_raises_with_invalid_query(self):
        """
        validate_request_against_schema() JSONSchemaValidationError on bad query
        """
        req_info = Data(
            path=self.req_path_info,
            method=self.method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data={
                'required_param': 'dummy',
                'optional_param': 'should be num'
            }
        )
        with self.assertRaises(JSONSchemaValidationError):
            validate_request_against_schema(req_info, self.spec)

    def test_validate_request_against_schema_api_key_only_param(self):
        """
        validate_request_against_schema() quiet on api_key only param list
        """
        # check ValidationError is not thrown
        query_data = {
            'api_key': 'dummy key',
        }
        req_info = Data(
            path=self.req_path_info,
            method=self.method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data=query_data
        )
        validate_request_against_schema(req_info, self.spec)

    def test_validate_request_against_schema_queryParameters_missing(
            self):
        """
        validate_request_against_schema() raises when queryParameters not
        defined in the specification
        """
        del self.spec['queryParameters']
        with self.assertRaises(JSONSchemaValidationError):
            validate_request_against_schema(self.parsed_data, self.spec)


class ResponseValidatorTestCase(ValidatorTestBase):

    def setUp(self):
        super(ResponseValidatorTestCase, self).setUp()
        self.Response = namedtuple('Request', 'content request status_code')
        self.data = u'{"data": { "uni": "¶" }}'
        self.request_obj = {
            'request_method': 'POST',
            'path_info': '/some/random/path'
        }
        self.status_code = 200
        self.response = self.Response(
            content=self.data,
            request=self.request_obj,
            status_code=self.status_code
        )

    def test_validate_response_against_schema_valid_instance(self):
        """
        validate_response_against_schema() quietly completes if valid.
        """
        # check ValidationError is not thrown
        validate_response_against_schema(self.response, self.spec)

    def test_validate_response_against_schema_raises_on_invalid_instance(self):
        """
        validate_response_against_schema() raises JSONSchemaValidationError.
        """
        data = u'{"data": []}'
        response = self.Response(
            content=data,
            request=self.request_obj,
            status_code=self.status_code
        )
        with self.assertRaises(JSONSchemaValidationError):
            validate_response_against_schema(response, self.spec)

    def test_validate_response_against_schema_raises_response_undefined(self):
        """
        validate_response_against_schema() raises ResponseNotDefinedError
        """
        self.raw_schema['resources'][0]['resources'][0]\
            ['methods'][1]['responses'] = {}
        spec = get_spec(self.parsed_data, self.raw_schema)
        with self.assertRaises(ResponseNotDefinedError):
            validate_response_against_schema(self.response, spec)


class GetSpecTestCase(ValidatorTestBase):

    def test__find_schema_deep_endpoint_past_uri_param(self):
        path_segments = {
            'remaining': ['/api', '/v5', '/test', '/fake_id:12', '/extended'],
            'path_info': '/api/v5/test/fake_id:12/extended'
        }

        sub_schema = _find_resource(self.raw_schema, path_segments)
        self.assertEqual(sub_schema['methods'][0]['method'], 'long')

    def test__find_schema_embedded_invalid_uri_param(self):
        path_segments = {
            'remaining': ['/api', '/v5', '/test', '/fake:12', '/extended'],
            'path_info': '/api/v5/test/fake:12/extended'
        }

        with self.assertRaises(UndefinedSchemaError):
            _find_resource(self.raw_schema, path_segments)

    def test__find_schema_uri_parameter(self):
        path_segments = {
            'remaining': ['/api', '/v5', '/test', '/fake_id:1001'],
            'path_info': '/api/v5/test/fake_id:1001'
        }
        sub_schema = _find_resource(self.raw_schema, path_segments)
        self.assertEqual(sub_schema['methods'][0]['method'], 'uri_param')

    def test__find_schema_invalid_uri_parameter(self):
        path_segments = {
            'remaining': ['/api', '/v5', '/test', '/fake_id:werd'],
            'path_info': '/api/v5/test/fake_id:werd'
        }
        with self.assertRaises(UndefinedSchemaError):
            _find_resource(self.raw_schema, path_segments)

    def test__find_schema_trailing_slash(self):
        path_segments = {
            'remaining': ['/api', '/v5', '/test', '/'],
            'path_info': '/api/v5/test/'
        }
        sub_schema = _find_resource(self.raw_schema, path_segments)
        self.assertEqual(sub_schema['methods'][0]['method'], 'delete')

    def test__find_schema_no_slash(self):
        path_segments = {
            'remaining': ['/api', '/v5', '/test'],
            'path_info': '/api/v5/test'
        }
        sub_schema = _find_resource(self.raw_schema, path_segments)
        self.assertEqual(sub_schema['methods'][0]['method'], 'short')

    def test_get_spec_success_without_endpoint_path(self):
        req_path_info = '/api/v5/test'
        method = 'short'
        request_info = Data(
            path=req_path_info,
            method=method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data=self.query_data
        )
        spec = get_spec(request_info, self.raw_schema)
        self.assertEqual(spec['method'], method)

    def test_get_spec_found_with_extended_path(self):
        req_path_info = '/api/v5/test/fake_id:1234567890/extended'
        method = 'long'
        request_info = Data(
            path=req_path_info,
            method=method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data=self.query_data
        )
        spec = get_spec(request_info, self.raw_schema)
        self.assertEqual(spec['method'], method)

    def test_get_spec_raises_when_method_not_found(self):
        """
        get_spec() raises UndefinedSchemaError
        """
        method = 'YAR'
        request_info = Data(
            path=self.req_path_info,
            method=method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data=self.query_data
        )
        with self.assertRaises(UndefinedSchemaError):
            get_spec(request_info, self.raw_schema)

    def test_get_spec_raises_when_endpoint_not_found(self):
        """
        get_spec() raises UndefinedSchemaError
        """
        self.raw_schema['resources'][0]['resources'][0]['relativeUri'] = '/-'
        with self.assertRaises(UndefinedSchemaError):
            get_spec(self.parsed_data, self.raw_schema)

    def test_get_spec_raises_when_resource_not_found(self):
        """
        get_spec() raises UndefinedSchemaError
        """
        req_path_info = '/api/v5/not_test/'
        request_info = Data(
            path=req_path_info,
            method=self.method,
            request_data=self.data['request'],
            response_data=self.data['response'],
            query_data=self.query_data
        )
        with self.assertRaises(UndefinedSchemaError):
            get_spec(request_info, self.raw_schema)


class GetPathSegmentsTestCase(unittest.TestCase):

    def test__get_path_segments_with_four_segments(self):
        """
        _get_path_segments() has correctly named segments with endpoint
        """
        req_path_info = '/api/v5/test/test:97'
        expected = {
            'remaining': ['/api', '/v5', '/test', '/test:97'],
            'path_info': '/api/v5/test/test:97'
        }
        result_segments = _get_path_segments(req_path_info)
        self.assertEquals(result_segments, expected)

    def test__get_path_segments_with_three_segments(self):
        """
        _get_path_segments() has correctly named segments without endpoint
        """
        req_path_info = '/api/v5/auth'
        expected = {
            'remaining': ['/api', '/v5', '/auth'],
            'path_info': '/api/v5/auth'
        }
        result_segments = _get_path_segments(req_path_info)
        self.assertEquals(result_segments, expected)


class ParserTestCase(unittest.TestCase):

    def setUp(self):
        qs = 'a_string=the%20string&a_number=1&list=a%20str%2C4&a_bool=true'
        self.request_w_boundary_string = {
            'path_info': '/api/v3/media/',
            'query_string': qs,
            'request_method': 'POST',
            'request': "{}",
            'response': "{}"
        }

    def test_parse_request_handles_query_string_types(self):
        """
        parse_data() parses types correctly from query string
        """
        request_info = parse_data(self.request_w_boundary_string)
        expected = {
            'a_number': 1,
            'list': ['a str', 4],
            'a_string': 'the string',
            'a_bool': True
        }
        self.assertEquals(request_info.query_data, expected)
        self.assertIsInstance(request_info.query_data['a_string'], str)
        self.assertIsInstance(request_info.query_data['list'], list)
        self.assertIsInstance(request_info.query_data['a_number'], int)

    def test_parse_request_handles_both_types_of_list_params(self):
        """
        parse_data() handles list param style `x=1&x=2`
        """
        qs = 'list_item=1&list_item=2&list_item=3'
        self.request_w_boundary_string['query_string'] = qs
        request_info = parse_data(self.request_w_boundary_string)
        expected = {'list_item': [1, 2, 3]}
        self.assertEquals(request_info.query_data, expected)
        self.assertIsInstance(request_info.query_data['list_item'], list)


class WhiteListTestCase(unittest.TestCase):

    def setUp(self):
        self.dummy_path = '/some/dummy/path/'
        self.dummy_method = 'DUMMY_METHOD'
        self.dummy_code = 999

        self.request = Object()
        setattr(self.request, 'request_method', self.dummy_method)
        setattr(self.request, 'path_info', self.dummy_path)

        self.response = Object()
        self.response.status_code = self.dummy_code
        self.response.request = self.request

        self.whitelist = [{'path': self.dummy_path}]

    def test_is_whitelisted_returns_false_request_path_not_found(self):
        setattr(self.request, 'path_info', '/some/unfound/path/')
        self.assertFalse(is_whitelisted(self.request, self.whitelist))

    def test_is_whitelisted_returns_true_request_matching_path(self):
        self.assertTrue(is_whitelisted(self.request, self.whitelist))

    def test_is_whitelisted_returns_true_response_matching_code(self):
        self.whitelist[0]['method'] = self.dummy_method
        self.whitelist[0]['code'] = self.dummy_code
        self.assertTrue(is_whitelisted(self.response, self.whitelist))

    def test_is_whitelisted_true_response_path_matched(self):
        self.assertTrue(is_whitelisted(self.response, self.whitelist))

    def test_is_whitelisted_returns_false_no_match_code(self):
        self.whitelist[0]['method'] = self.dummy_method
        self.whitelist[0]['code'] = 'WONT_MATCH'
        self.assertFalse(is_whitelisted(self.response, self.whitelist))

    def test_is_whitelisted_returns_true_request_match_method(self):
        self.whitelist[0]['method'] = self.dummy_method
        self.assertTrue(is_whitelisted(self.request, self.whitelist))

    def test_is_whitelisted_returns_false_request_no_match_method(self):
        setattr(self.request, 'request_method', 'INVALID_METHOD')
        self.whitelist[0]['method'] = self.dummy_method
        self.assertFalse(is_whitelisted(self.request, self.whitelist))

    def test_is_whitelisted_returns_true_request_with_many_whitelist(self):
        path_match = '/match/me/'
        method_match = 'MATCH'
        self.whitelist.append({'path': '/path/2', 'method': 'method2'})
        self.whitelist.append({'path': '/path/3', 'method': 'method3'})
        self.whitelist.append({'path': path_match, 'method': method_match})
        self.whitelist.append({'path': '/path/4', 'method': 'method4'})
        setattr(self.request, 'path_info', path_match)
        setattr(self.request, 'request_method', method_match)
        self.assertTrue(is_whitelisted(self.request, self.whitelist))

    def test_when_regex_is_not_greedy(self):
        whitelist = [{'path': '^/some/path/long$'}]
        setattr(self.request, 'path_info', '/some/path/longer')
        self.assertFalse(is_whitelisted(self.request, whitelist))

    def test_when_regex_is_greedy(self):
        whitelist = [{'path': '/some/path/long'}]
        setattr(self.request, 'path_info', '/some/path/longer')
        self.assertTrue(is_whitelisted(self.request, whitelist))
