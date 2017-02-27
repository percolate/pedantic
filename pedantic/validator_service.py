"""Some placeholder module text"""

import os
import logging
import unittest
import json

import yaml
from flask import Flask, request, g, flash, jsonify
from flask import Request as FlaskRequest
from werkzeug.datastructures import Headers
from requests import Request, Session
from vcrpy import vcr
from vcrpy.vcr.errors import CannotOverwriteExistingCassetteException

import cStringIO  # TEMPORARY


app = Flask(__name__)


_missing = object()


def _get_data(req, cache):
    getter = getattr(req, 'get_data', None)
    if getter is not None:
        return getter(cache=cache)
    return req.data


def get_json(self, force=False, silent=False, cache=True):
    rv = getattr(self, '_cached_json', _missing)
    if rv is not _missing:
        return rv

    if not (force or self.is_json):
        return None

    request_charset = self.mimetype_params.get('charset')
    try:
        data = _get_data(self, cache)
        print('HERE BE DATA: {}'.format(data))
        if not data:
            data = "{}"
        print("DOING JSON THANG")
        if request_charset is not None:
            rv = json.loads(data, encoding=request_charset)
        else:
            rv = json.loads(data)
    except ValueError as e:
        if silent:
            rv = None
        else:
            rv = self.on_json_loading_failed(e)
    if cache:
        self._cached_json = rv
    print('YO mADE TI TO THE END')
    return rv

FlaskRequest.get_json = get_json
app.request_class = FlaskRequest

proxy_destination = None
active_service_title = None
active_contract_name = None
contracts_directory = None
record_mode = 'new_episodes'


class ContractPlayer(object):
    """Some placeholder ContractPlayer text"""

    def _test_generator(self, detail):
        def make_cassette_request(request_cassette):
            data = request_cassette['body']
            url = request_cassette['uri']
            method = request_cassette['method']
            headers = request_cassette['headers']
            headers = {key: headers[key][0] for key in headers}

            s = Session()
            req = Request(method, url, data=data, headers=headers)
            prepared_req = req.prepare()
            resp = s.send(prepared_req)
            return resp

        def test(self):
            for interaction in detail['interactions']:
                request_cassette = interaction['request']
                response_cassette = interaction['response']
                response = make_cassette_request(request_cassette)
                expected_body = response_cassette['body']['string']
                expected_code = response_cassette['status']['code']
                headers = response_cassette['headers']

                # sanitize response headers for comparison
                expected_headers = {key: headers[key][0] for key in headers
                                    if key != 'date'}
                response_headers = {key: response.headers[key]
                                    for key in response.headers
                                    if key != 'date'}

                self.assertEqual(
                    expected_body, response.content.decode('UTF-8'),
                    msg='Response body does not match contract.'
                        '\n\nExpected:\n{}\n\nActual:\n{}'.format(
                         expected_body, response.content)
                )
                self.assertEqual(
                    expected_code, response.status_code,
                    msg='Response status code does not match contract.'
                        '\n\nExpected:\n{}\n\nActual:\n{}'.format(
                         expected_code, response.status_code)
                )
                if False:  # TODO Allow header comparison
                    self.assertEqual(
                        expected_headers, response_headers,
                        msg='Response headers do not match contract.'
                            '\n\nExpected:\n{}\n\nActual:\n{}'.format(
                             expected_headers, response_headers)
                    )

        return test

    def run_contracts(self, contracts_dir):
        test_suite = unittest.TestSuite()
        contracts = {}
        for root, dirs, files in os.walk(contracts_dir, topdown=False):
            for name in files:
                with open(os.path.join(root, name)) as f:
                    contracts[name] = yaml.load(f.read())

        for name, contract in contracts.items():
            class TestClass(unittest.TestCase):
                pass

            test_name = 'test_{}'.format(name)
            test_method = self._test_generator(contract)
            test_method.__name__ = test_name
            setattr(TestClass, test_method.__name__, test_method)
            test = unittest.defaultTestLoader.loadTestsFromTestCase(TestClass)
            test_suite.addTest(test)
        runner = unittest.TextTestRunner()
        return runner.run(test_suite)


def set_proxy_settings(serv_title, dest, ctr_name, ctr_dir, rec_mode=False):
    global active_service_title
    global proxy_destination
    global active_contract_name
    global contracts_directory
    global record_mode

    active_service_title = serv_title
    proxy_destination = dest
    active_contract_name = ctr_name
    contracts_directory = ctr_dir
    if rec_mode:
        record_mode = 'none'
    else:
        record_mode = 'new_episodes'


@app.route('/', defaults={'path': ''},
           methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@app.route('/<path:path>',
           methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def validator(path):
    """
    .. http:any:: /

        This route listens for any request and proxies to the *Provider*
        service set in *proxy_destination*.  The request and subsequent
        response are stored as a contract.

        **Example request**:

        .. code-block:: bash

            curl -i http://localhost:5000/some_endpoint

        :qparam string path: URL path following *http://localhost:5000/*

        :return: The response returned to the proxy.

    """
    print("End.\n\n\nStart...")

    if (proxy_destination is None
        or active_service_title is None
        or active_contract_name is None):
        return ('No recording in progress', 400)

    # VCR settings
    logging.basicConfig()  # initialize logging to show vcrpy debug info
    vcr_log = logging.getLogger('vcr')
    vcr_log.setLevel(logging.INFO)
    contract_dir = os.path.join(str(contracts_directory), 'contracts', active_service_title)
    my_vcr = vcr.VCR(
        cassette_library_dir=contract_dir,
        record_mode=record_mode,
        match_on=['method', 'scheme', 'host', 'port', 'path', 'query', 'raw_body']
    )

    @my_vcr.use_cassette()
    def make_request(url, request):
        # TEMPORARY
        def temp(e):
            return e.message

        request.on_json_loading_failed = temp

        stream = None
        value = None  # DELETE Eventually
        json = None

        if not request.is_json:
            stream = request.stream
            value = stream.getvalue()
            # recreate cString, so we can read it
            stream = cStringIO.StringIO(value)
        else:
            try:
                # Munge JSON for Requests library
                json = request.get_json()
            except Exception as e:
                print(e)

        data = request.data
        params = dict(request.args)
        method = request.method
        form = request.form
        files = request.files
        headers = request.headers
        cookies = request.cookies

        print("Params: {}".format(params))
        print("Data: {}".format(request.data))
        print("Files: {}".format(request.files))
        print("Form: {}".format(form))
        print("Cookies: {}".format(cookies))
        print("Stream: {}".format(value))
        print("JSON: {}".format(json))

        # request.headers is immutable, so we create our own mutable version
        hdrs = Headers()
        for header in headers.to_list():
            hdrs.add(header[0], header[1])

        # Remove content length if empty (empty creates BAD REQUEST errors)
        if not hdrs.get('Content-Length'):
            hdrs.remove('Content-Length')

        # Set Host to intended destination
        hdrs.set('Host', url.split('/')[2])

        s = Session()
        print('GOT HERE, JUST BEFORE REQ')
        resp = s.request(
            method,
            url,
            data=data,
            files=files,
            stream=stream,
            json=json,
            headers=hdrs,
            params=params,
            cookies=cookies,
        )
        # prepared_req = req.prepare()
        # resp = s.send(prepared_req)
        print('GOT HERE, JUST AFTER REQ')
        return (resp.content, resp.status_code, resp.headers.items())

    url = '{}/{}'.format(proxy_destination, path)

    make_request.__name__ = '{}.yaml'.format(active_contract_name)
    try:
        resp = make_request(url, request)
    except CannotOverwriteExistingCassetteException:
        resp = 'No cassette for this request.', 404
    return resp
