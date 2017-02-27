import unittest

from pedantic import validator_service as val  # shared across tests


def setup_validator():
    val.app.config['TESTING'] = True
    app = val.app.test_client()
    return app


class TestPedantic(unittest.TestCase):

    def setUp(self):
        pass

    def test_run_contracts_with_valid_contracts(self):
        pass
