Skelerest Plugin
---

A plugin for Skelebot that allows for pre-configured and parameterized REST commands to be executed.

---

[![CircleCI token](https://circleci.com/gh/carsdotcom/skelerest-sb-plugin/tree/main.svg?style=svg)](https://circleci.com/gh/carsdotcom/skelerest-sb-plugin)
[![codecov](https://codecov.io/gh/carsdotcom/skelerest-sb-plugin/branch/main/graph/badge.svg)](https://codecov.io/gh/carsdotcom/skelerest-sb-plugin)
[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE)

### Configuration

Different REST requests can be configured in the `components.skelerest` section of the Skelebot
YAML once the plugin has been installed. Requests can be configure for GET, POST, PUT, and DELETE
methods. Values in the requests (endpoint, params, headers, and body) can be parameterized using
curly braces using the following syntax: ({variable_name:default_value}). The default value, as
well as the preceding colon are optional. If the variable is provided without a default value, it
will be required by the associated Skelebot CLI command.

The example below creates four different Skelebot CLI commands with an assortment of variables.

```
components:
  skelerest:
    requests:
    - name: metadata
      endpoint: "http://127.0.0.1:5000/{endpoint:quotes}"
      method: GET
      aws: True
      awsProfile: "dev"
      awsRegion: "us-east-1"
      params:
        - name: api_version
          value: "{api_version}"
      headers:
        - name: name
          value: "{name:my-name}"
        - name: username
          value: "{username:me}"
    - name: metadata
      endpoint: "http://127.0.0.1:5000/{endpoint:quotes}"
      method: POST
      params:
        - name: api_version
          value: "{api_version}"
        - name: username
          value: "{username:my-username}"
      headers:
        - name: name
          value: "{name:my-name}"
      body: metadata.json
    - name: metadata
      endpoint: "http://127.0.0.1:5000/{endpoint:quotes}/{id}"
      method: PUT
      headers:
        - name: name
          value: "{name:my-name}"
      body:
        id: pricing
        version: "{version:0.1.0}"
    - name: metadata
      endpoint: "http://127.0.0.1:5000/{endpoint:quotes}/{id}"
      method: DELETE
      params:
        - name: api_version
          value: "{api_version}"
```

### Usage

Requests that are configured in the yaml can then be called via Skelebot. The request is initiated
by providing it's configured name placed after the `{method}-` prefix. Each request is associated
with it's own command in Skelebot, allowing for the parameterized variables in the request to be
examined via the help command.

```
>> skelebot get-metadata --help
```

The following command would trigger the a GET request ...

```
>> skelebot get-metadata --name test --username test-test --api_version 1.2.3
|SKELEREST| Executing : GET http://127.0.0.1:5000/quotes?api_version=1.2.3
|SKELEREST| HEADERS
|SKELEREST| - name : test
|SKELEREST| - username : test-test
|SKELEREST| SUCCESS: 200
```

### AWS Auth

As shown in the `GET` request example above, the Skelerest plugin supports AWS Authorized requests.

This can be turned on by setting the `aws` field to `True` in the config for the specific request.
By default Skelerest will use the default profile and the `us-east-1` region, but these values can
be manually specifed using the `awsProfile` and `awsRegion` fields respectively.

### Example

In the `example/` folder a simple project has been setup that can be used as an example for how to
use the Skelerest plugin to make REST requests. The API here exposes four endpoints for GET, POST,
PUT, and DELETE. A Skelebot.yaml config has already been setup to make requests against each
endpoint and there is a single Skelebot job setup to run the API in Docker on port 5000.


In the `example/` folder, use the `run_api` job to start the test API in Docker on port 5000.
```
>> skelebot run_api
```

Once the API is up and running, requests can be made through the skelerest plugin.
```
>> skelebot get-notes
|SKELEREST| GET http://127.0.0.1:5000/notes
|SKELEREST| PARAMS
|SKELEREST| HEADERS
|SKELEREST| SUCCESS: 200
|SKELEREST| {
|SKELEREST|   "notes": {
|SKELEREST|     "1": "Finish Writing Code",
|SKELEREST|     "2": "Go to the Store",
|SKELEREST|     "3": "Mow the Lawn"
|SKELEREST|   }
|SKELEREST| }
|SKELEREST|
```
