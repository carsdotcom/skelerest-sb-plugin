import argparse
import unittest
import copy
from unittest import mock
from schema import SchemaError
from ..skelerest import Skelerest

class TestSkelerest(unittest.TestCase):

    CONFIG_VALID = {
        "requests": [
            {
                "name": "test-project",
                "endpoint": "http://not a real {site}",
                "method": "POST",
                "params": [
                    {"name": "one", "value": "{param-one:1}"},
                    {"name": "two", "value": "{param-two:2}"}
                ],
                "headers": [
                    {"name": "a", "value": "{header-one:A}"},
                    {"name": "b", "value": "{header-two:B}"}
                ],
                "body": {
                    "id": "{id:0}",
                    "name": "test",
                    "items": ["a", "b", "c"],
                    "parent": {
                        "id": "{parent-id}",
                        "name": "{parent-name}"
                    }
                }
            }, {
                "name": "test-project",
                "endpoint": "http://not a real {site}",
                "method": "PUT",
                "params": [
                    {"name": "one", "value": "{param-one:1}"},
                    {"name": "two", "value": "{param-two:2}"}
                ],
                "headers": [
                    {"name": "a", "value": "{header-one:A}"},
                    {"name": "b", "value": "{header-two:B}"}
                ],
                "body": {
                    "id": "{id:0}",
                    "name": "test",
                    "items": ["a", "b", "c"],
                    "parent": {
                        "id": "{parent-id}",
                        "name": "{parent-name}"
                    }
                }
            }, {
                "name": "test-project",
                "endpoint": "http://not a real {site}",
                "method": "GET",
                "params": [
                    {"name": "one", "value": "{param-one:1}"},
                    {"name": "two", "value": "{param-two:2}"}
                ],
                "headers": [
                    {"name": "a", "value": "{header-one:A}"},
                    {"name": "b", "value": "{header-two:B}"}
                ]
            }, {
                "name": "test-project",
                "endpoint": "http://not a real {site}",
                "method": "DELETE",
                "params": [
                    {"name": "one", "value": "{param-one:1}"},
                    {"name": "two", "value": "{param-two:2}"}
                ],
                "headers": [
                    {"name": "a", "value": "{header-one:A}"},
                    {"name": "b", "value": "{header-two:B}"}
                ]
            }
        ]
    }

    CONFIG_INVALID = {
        "requests": 0
    }

    def test_load(self):
        skelerest = Skelerest.load(self.CONFIG_VALID)

        self.assertEqual(len(skelerest.requests), 4)
        self.assertEqual(skelerest.commands, ["post-test-project", "put-test-project", "get-test-project", "delete-test-project"])

    def test_load_invalid_schema(self):
        try:
            Skelerest.load(self.CONFIG_INVALID)
            self.fail("Invalid Config Exception Expected")
        except SchemaError as error:
            self.assertEqual(str(error), "Skelerest 'requests' must be a list")

    def test_add_parsers(self):
        skelerest = Skelerest.load(self.CONFIG_VALID)

        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(dest="job")
        subparsers = skelerest.addParsers(subparsers)
        post_parser = subparsers.choices["post-test-project"]
        post_parser.parse_args([
            '--site', 'site',
            '--param-one', '01', '--param-two', '02',
            '--header-one', 'AA', '--header-two', 'BB',
            '--id', '1', '--parent-id', '2', '--parent-name', 'you'
        ])
        get_parser = subparsers.choices["get-test-project"]
        get_parser.parse_args([
            '--param-one', '01', '--param-two', '02',
            '--header-one', 'AA', '--header-two', 'BB',
            '--site', 'site'
        ])

        self.assertNotEqual(post_parser, None)
        self.assertNotEqual(get_parser, None)

    @mock.patch('skelerest.skelerest.request_api')
    def test_execute_get(self, mock_req_api):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_req_api.get.return_value = mock_response

        skelerest = Skelerest.load(self.CONFIG_VALID)

        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(dest="job")
        subparsers = skelerest.addParsers(subparsers)
        args = parser.parse_args([
            'get-test-project',
            '--param-one', '01', '--param-two', '02',
            '--header-one', 'AA', '--header-two', 'BB',
            '--site', 'site'
        ])

        skelerest.execute(None, args)

        endpoint = "http://not a real site"
        params = {'one': '01', 'two': '02'}
        headers = {'a': 'AA', 'b': 'BB'}
        mock_req_api.get.assert_called_with(endpoint, params=params, headers=headers)

    @mock.patch('skelerest.aws_auth.datetime')
    @mock.patch('skelerest.aws_auth.get_credentials')
    @mock.patch('skelerest.aws_auth.hash')
    @mock.patch('skelerest.aws_auth.sign')
    @mock.patch('skelerest.skelerest.request_api')
    def test_execute_aws_auth(self, mock_req_api, mock_sign, mock_hash, mock_cred, mock_dtime):
        mock_hash.return_value = "hashed"

        mock_date = mock.MagicMock()
        mock_date.strftime.return_value = "2022-01-01"
        mock_dtime.datetime.utcnow.return_value = mock_date

        mock_signed = mock.MagicMock()
        mock_signed.digest.return_value = "signed"
        mock_signed.hexdigest.return_value = "hex-signed"
        mock_sign.return_value = mock_signed

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_req_api.get.return_value = mock_response

        mock_creds = mock.MagicMock()
        mock_creds.access_key = "akey"
        mock_creds.secret_key = "skey"
        mock_cred.return_value = mock_creds

        config = copy.deepcopy(self.CONFIG_VALID)
        config.get("requests")[2]["aws"] = True
        config.get("requests")[2]["awsProfile"] = "data-dev"
        config.get("requests")[2]["awsRegion"] = "us-east-2"

        skelerest = Skelerest.load(config)

        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(dest="job")
        subparsers = skelerest.addParsers(subparsers)
        args = parser.parse_args([
            'get-test-project',
            '--param-one', '01', '--param-two', '02',
            '--header-one', 'AA', '--header-two', 'BB',
            '--site', 'site'
        ])

        skelerest.execute(None, args)

        endpoint = "http://not a real site"
        params = {'one': '01', 'two': '02'}
        headers = {'a': 'AA', 'b': 'BB', 'content-type': 'application/json', 'x-amz-date': '2022-01-01', 'Authorization': 'AWS4-HMAC-SHA256 Credential=akey/2022-01-01/us-east-2/execute-api/aws4_request, SignedHeaders=content-type;host;x-amz-date, Signature=hex-signed'}
        mock_req_api.get.assert_called_with(endpoint, params=params, headers=headers)

    @mock.patch('skelerest.skelerest.request_api')
    def test_execute_post(self, mock_req_api):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_req_api.post.return_value = mock_response

        skelerest = Skelerest.load(self.CONFIG_VALID)

        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(dest="job")
        subparsers = skelerest.addParsers(subparsers)
        args = parser.parse_args([
            'post-test-project',
            '--site', 'post',
            '--param-one', '01', '--param-two', '02',
            '--header-one', 'AA', '--header-two', 'BB',
            '--id', '1', '--parent-id', '2', '--parent-name', 'you'
        ])

        skelerest.execute(None, args)

        endpoint = "http://not a real post"
        params = {'one': '01', 'two': '02'}
        headers = {'a': 'AA', 'b': 'BB'}
        data = '{"id": "1", "name": "test", "items": ["a", "b", "c"], "parent": {"id": "2", "name": "you"}}'
        mock_req_api.post.assert_called_with(endpoint, data=data, params=params, headers=headers)

    @mock.patch('skelerest.skelerest.request_api')
    def test_execute_put(self, mock_req_api):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_req_api.put.return_value = mock_response

        skelerest = Skelerest.load(self.CONFIG_VALID)

        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(dest="job")
        subparsers = skelerest.addParsers(subparsers)
        args = parser.parse_args([
            'put-test-project',
            '--site', 'put',
            '--param-one', '01', '--param-two', '02',
            '--header-one', 'AA', '--header-two', 'BB',
            '--id', '123', '--parent-id', '2', '--parent-name', 'you'
        ])

        skelerest.execute(None, args)

        endpoint = "http://not a real put"
        params = {'one': '01', 'two': '02'}
        headers = {'a': 'AA', 'b': 'BB'}
        data = '{"id": "123", "name": "test", "items": ["a", "b", "c"], "parent": {"id": "2", "name": "you"}}'
        mock_req_api.put.assert_called_with(endpoint, data=data, params=params, headers=headers)

    @mock.patch('skelerest.skelerest.request_api')
    def test_execute_delete(self, mock_req_api):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_req_api.delete.return_value = mock_response

        skelerest = Skelerest.load(self.CONFIG_VALID)

        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(dest="job")
        subparsers = skelerest.addParsers(subparsers)
        args = parser.parse_args([
            'delete-test-project',
            '--param-one', '01', '--param-two', '02',
            '--header-one', 'AAA', '--header-two', 'BBB',
            '--site', 'site'
        ])

        skelerest.execute(None, args)

        endpoint = "http://not a real site"
        params = {'one': '01', 'two': '02'}
        headers = {'a': 'AAA', 'b': 'BBB'}
        mock_req_api.delete.assert_called_with(endpoint, params=params, headers=headers)

    @mock.patch('skelerest.skelerest.request_api')
    def test_execute_error_response(self, mock_req_api):
        mock_response = mock.MagicMock()
        mock_response.status_code = 400
        mock_response.ok = False
        mock_req_api.get.return_value = mock_response

        skelerest = Skelerest.load(self.CONFIG_VALID)

        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(dest="job")
        subparsers = skelerest.addParsers(subparsers)
        args = parser.parse_args([
            'get-test-project',
            '--param-one', '01', '--param-two', '02',
            '--header-one', 'AA', '--header-two', 'BB',
            '--site', 'site'
        ])

        try:
            skelerest.execute(None, args)
            self.fail("Invalid REST Response Code Expected")
        except:
            endpoint = "http://not a real site"
            params = {'one': '01', 'two': '02'}
            headers = {'a': 'AA', 'b': 'BB'}
            mock_req_api.get.assert_called_with(endpoint, params=params, headers=headers)

