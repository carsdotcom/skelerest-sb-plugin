import unittest
from schema import SchemaError
from ..rest_request import RestRequest

class TestRestRequest(unittest.TestCase):

    CONFIG_VALID = {
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
    }

    CONFIG_INVALID = {
        "endpoint": 0,
        "method": 123,
        "params": "test",
        "headers": "test",
        "body": 123
    }

    def test_load(self):
        restRequest = RestRequest.load(self.CONFIG_VALID)

        self.assertEqual(restRequest.name, "test-project")
        self.assertEqual(restRequest.endpoint, "http://not a real {site}")
        self.assertEqual(restRequest.method, "POST")

        i = 0
        exp_param_names = ["one", "two"]
        exp_param_values = ["{param-one:1}", "{param-two:2}"]
        for param in restRequest.params:
            self.assertEqual(param.name, exp_param_names[i])
            self.assertEqual(param.value, exp_param_values[i])
            i += 1

        i = 0
        exp_header_names = ["a", "b"]
        exp_header_values = ["{header-one:A}", "{header-two:B}"]
        for header in restRequest.headers:
            self.assertEqual(header.name, exp_header_names[i])
            self.assertEqual(header.value, exp_header_values[i])
            i += 1

        self.assertEqual(restRequest.body["id"], "{id:0}")
        self.assertEqual(restRequest.body["name"], "test")
        self.assertEqual(restRequest.body["parent"]["id"], "{parent-id}")
        self.assertEqual(restRequest.body["parent"]["name"], "{parent-name}")

        i = 0
        exp_items = ["a", "b", "c"]
        for item in restRequest.body["items"]:
            self.assertEqual(item, exp_items[i])
            i += 1

        i = 0
        exp_var_names = ["site", "param-one", "param-two",
                    "header-one", "header-two", "id", "parent-id", "parent-name"]
        exp_var_defaults = [None, "1", "2", "A", "B", "0", None, None]
        exp_var_locations = [
            RestRequest.RestVar.Location.ENDPOINT,
            RestRequest.RestVar.Location.PARAMS,
            RestRequest.RestVar.Location.PARAMS,
            RestRequest.RestVar.Location.HEADERS,
            RestRequest.RestVar.Location.HEADERS,
            RestRequest.RestVar.Location.BODY,
            RestRequest.RestVar.Location.BODY,
            RestRequest.RestVar.Location.BODY
        ]
        for var in restRequest.variables:
            self.assertEqual(var.name, exp_var_names[i])
            self.assertEqual(var.default, exp_var_defaults[i])
            self.assertEqual(var.location, exp_var_locations[i])
            i += 1

    def test_load_invalid_schema(self):
        try:
            RestRequest.load(self.CONFIG_INVALID)
            self.fail("Invalid Config Exception Expected")
        except SchemaError as error:
            self.assertEqual(str(error), "SkeleRequest 'endpoint' must be a String")

    def test_body_file(self):
        cfg = self.CONFIG_VALID
        cfg["body"] = "skelerest/test/files/body.json"
        restRequest = RestRequest.load(self.CONFIG_VALID)

        self.assertEqual(restRequest.body["id"], "{id:0}")
        self.assertEqual(restRequest.body["name"], "test")
        self.assertEqual(restRequest.body["parent"]["id"], "{parent-id}")
        self.assertEqual(restRequest.body["parent"]["name"], "{parent-name}")

        i = 0
        exp_items = ["a", "b", "c"]
        for item in restRequest.body["items"]:
            self.assertEqual(item, exp_items[i])
            i += 1

    def test_params_dict(self):
        restRequest = RestRequest.load(self.CONFIG_VALID)
        params_dict = restRequest.get_params_dict()

        self.assertEqual(str(params_dict), "{'one': '{param-one:1}', 'two': '{param-two:2}'}")

    def test_headers_dict(self):
        restRequest = RestRequest.load(self.CONFIG_VALID)
        headers_dict = restRequest.get_headers_dict()

        self.assertEqual(str(headers_dict), "{'a': '{header-one:A}', 'b': '{header-two:B}'}")

if __name__ == '__main__':
    unittest.main()
