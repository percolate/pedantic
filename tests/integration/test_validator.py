from __future__ import absolute_import, unicode_literals
import unittest
import os
import sys
import json
from copy import deepcopy

from pedantic import validator_service as val  # shared across tests

schema_file = 'example_schema.json'
with open(os.path.join(sys.path[0], schema_file), 'r') as f:
    read_data = f.read()
SCHEMAS = read_data


whitelist_file = 'example_whitelist.json'
with open(os.path.join(sys.path[0], whitelist_file), 'r') as f:
    read_data = f.read()
WHITELIST = read_data


def setup_validator():
    val.app.config['TESTING'] = True
    app = val.app.test_client()
    return app


class TestPedantic(unittest.TestCase):

    def setUp(self):
        self.app = setup_validator()
        val.set_proxy_settings(deepcopy(SCHEMAS), deepcopy(WHITELIST))

    def test_validator_returns_error_missing_content_type(self):
        resp = self.app.post('/', data='no content type')
        data = json.loads(resp.data.decode('utf8'))['error']
        self.assertIn('Content-Type', data)
        self.assertEqual(resp.status_code, 400)

    def test_validator_parse_data_error_response(self):
        resp = self.app.post(
            '/',
            data=json.dumps({}),
            content_type='application/json'
        )
        data = json.loads(resp.data.decode('utf8'))['error']
        self.assertIn('required', data)
        self.assertEqual(resp.status_code, 400)

    def test_validator_whitelist_response(self):
        resp = self.app.post(
            '/',
            data=json.dumps({
                "method": "POST",
                "path_info": "/whitelisted/path",
                "status_code": 200,
                "response": {'some': 'thing'}
            }),
            content_type='application/json'
        )
        data = json.loads(resp.data.decode('utf8'))['warning']
        self.assertIn('whitelisted', data)
        self.assertEqual(resp.status_code, 200)

    def test_validator_UndefinedSchemaError_response(self):
        resp = self.app.post(
            '/',
            data=json.dumps({
                "method": "RAWR",
                "path_info": "/",
                "request": {}
            }),
            content_type='application/json'
        )
        data = json.loads(resp.data.decode('utf8'))['error']
        self.assertIn('not found', data)
        self.assertEqual(resp.status_code, 400)

    def test_validator_request_validation_error(self):
        resp = self.app.post(
            '/',
            data=json.dumps({
                "method": "POST",
                "path_info": "/api/v5/test/",
                "request": {'unspecified': 'fake'}
            }),
            content_type='application/json'
        )
        data = json.loads(resp.data.decode('utf8'))['error']
        self.assertIn('request validation', data)
        self.assertEqual(resp.status_code, 400)

    def test_validator_response_validation_error(self):
        resp = self.app.post(
            '/',
            data=json.dumps({
                "method": "POST",
                "path_info": "/api/v5/test/",
                "status_code": 200,
                "response": {'data': 'is not an object as specified'}
            }),
            content_type='application/json'
        )
        data = json.loads(resp.data.decode('utf8'))['error']
        self.assertIn('response validation', data)
        self.assertEqual(resp.status_code, 400)

    def test_validator_happy_validation_time(self):
        resp = self.app.post(
            '/',
            data=json.dumps({
                "method": "POST",
                "path_info": "/api/v5/test/",
                "request": {}
            }),
            content_type='application/json'
        )
        data = json.loads(resp.data.decode('utf8'))['message']
        self.assertIn('All is well', data)
        self.assertEqual(resp.status_code, 200)
