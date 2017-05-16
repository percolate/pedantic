from __future__ import absolute_import, unicode_literals
import unittest
import json
import subprocess
import requests

pedantic_server_process = None

port = '31234'
service_url = 'http://localhost:{}'.format(port)


def setUpModule():
    # Prop up the Pedantic service to request against.
    # It's brutal and hackish, but gets us an end to end test
    global pedantic_server_process
    pedantic_server_process = subprocess.Popen(
        "./pedantic.py tests/example_schema.json "
        "--whitelist=tests/example_whitelist.json --port={}".format(port),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    waiting = True
    while waiting:
        if pedantic_server_process.stdout:
            line = pedantic_server_process.stdout.readline()
            if port in str(line):  # the server has finished starting
                waiting = False


def tearDownModule():
    pedantic_server_process.kill()


class TestRunningServer(unittest.TestCase):

    def test_whitelist_with_custom_port_on_running_service(self):
        payload = {
            "method": "POST",
            "path_info": "/whitelisted/path/",
            "status_code": 200,
            "response": {
                "x": "data"
            }
        }
        resp = requests.post(service_url, json=payload)
        content = json.loads(resp.content.decode('utf8'))
        self.assertIsNotNone(content['warning'])
        self.assertEqual(resp.status_code, 200)

    def test_invalid_local_schema_on_running_service(self):
        payload = {
            "method": "POST",
            "path_info": "/api/v5/test/",
            "query_string": "does_not=matter",
            "request": {"x": {"not": "a string"}},
            "response": "not an object"
        }
        resp = requests.post(service_url, json=payload)

        content = json.loads(resp.content.decode('utf8'))
        self.assertIn('Pedantic error', content['error'])
        self.assertEqual(resp.status_code, 400)

    def test_invalid_foreign_schema_on_running_service(self):
        payload = {
            "method": "POST",
            "path_info": "/api/v5/test/",
            "status_code": 200,
            "query_string": "does_not=matter",
            "request": {"x": {"not": "a string"}},
            "response": {"data": "not an object"}
        }
        resp = requests.post(service_url, json=payload)

        content = json.loads(resp.content.decode('utf8'))
        self.assertIn('request validation', content['error'])
        self.assertIn('response validation', content['error'])
        self.assertEqual(resp.status_code, 400)

    def test_valid_local_and_foreign_schemas_on_running_service(self):
        payload = {
            "method": "POST",
            "path_info": "/api/v5/test/",
            "query_string": "required_param=a_string,optional_param=1",
            "status_code": 200,
            "request": {"x": "data"},
            "response": {"data": {"any": "thing"}}
        }
        resp = requests.post(service_url, json=payload)
        content = json.loads(resp.content.decode('utf8'))
        self.assertIsNotNone(content['message'])
        self.assertEqual(resp.status_code, 200)
