import json
import ast
import boto3
import requests as request_api
import sys, os, base64, datetime, hashlib, hmac
from schema import Schema, And, Optional
from skelebot.objects.component import Activation, Component
from skelebot.objects.skeleYaml import SkeleYaml
from .rest_request import RestRequest

COMMAND_TEMPLATE = "{method}-{name}"

class Skelerest(Component):
    """ Component Class for configuring and executing REST reqeuests through Skelebot """

    activation = Activation.CONFIG
    commands = None

    schema = Schema({
        'requests': And(list, error='Skelerest \'requests\' must be a list')
    }, ignore_extra_keys=True)

    requests = None

    def __init__(self, requests=None):
        """
        Initialize the Skelerest Component with the list of requests

        Parameters
        ----------
        requests : list<RestRequest>
            list of RestRequest objects to perform CRUD operations in an API
        """

        self.requests = {}
        for req in requests:
            self.requests[COMMAND_TEMPLATE.format(method=req.method.lower(), name=req.name)] = req

        self.commands = list(self.requests.keys())

    def __display(self, message):
        """
        Print a single message with a 'skelerest' prefix

        Parameters
        ----------
        message : str
            The message to be displayed via a  print command
        """

        message = message.replace("\n", "\n|SKELEREST| ")
        print(f"|SKELEREST| {message}")

    def __show_execution(self, method, endpoint, params, headers, body):
        """
        Display the execution of the REST command for the user

        Parameters
        ----------
        method : str
            The REST method used in the API request (GET, POST, PUT, or DELETE)
        endpoint : str
            The http URI endpoint through which the API can be accessed
        params : dict
            A dict of the query parameters used in the REST request
        headers : dict
            A dict of the header parameters used in the REST request
        body : dict
            A Dictionary representing the POST/PUT body of the request
        """

        self.__display(f"{method} {endpoint}")
        self.__display(f"PARAMS")
        for name, value in params.items():
            self.__display(f"- {name} : {value}")
        self.__display(f"HEADERS")
        for name, value in headers.items():
            self.__display(f"- {name} : {value}")
        if (body != "None"):
            self.__display(f"BODY:\n{body}")

    def addParsers(self, subparsers):
        """
        Add argument parsers for each request in the configured in the component

        Each request in the component is translated to a command in the Skelebot CLI using the
        REST method and the name provided for the request (get-my-api-data). For each request
        there are parameters generated from all scanned variables in the configuration. These are
        optional parameters unless a default value is specified.

        Parameters
        ----------
        subparsers : ArgumentParser
            The ArgumentParser in Skelebot on which the Skelerest commands will be added
        """

        for cmd, req in self.requests.items():
            help_message = f"{req.method.upper()} to {req.endpoint}"
            restparser = subparsers.add_parser(cmd, help=help_message)
            for var in req.variables:
                name = f"--{var.name}"
                if (var.default is None):
                    restparser.add_argument(name, required=True, help="REQUIRED")
                else:
                    restparser.add_argument(name, default=var.default, help=f"DEFAULT: {var.default}")

        return subparsers

    def __clean_body(self, body):
        #TODO: doc
        body = body.replace("'", "\"")
        body = body.replace("True", "true")
        body = body.replace("False", "false")
        return body

    def __sign(self, key, msg):
        #TODO: doc
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def __get_signature_key(self, key, date_stamp, regionName, serviceName):
        #TODO: doc
        kDate = self.__sign(('AWS4' + key).encode('utf-8'), date_stamp)
        kRegion = self.__sign(kDate, regionName)
        kService = self.__sign(kRegion, serviceName)
        kSigning = self.__sign(kService, 'aws4_request')
        return kSigning

    def __get_aws_headers(self, endpoint, profile, region, method, body, params, headers):
        #TODO: doc
        #TODO: cleanup, this shit is ugly (thanks, Bezos)
        #TODO: Unit Tests
        endpoint_parts = endpoint.replace("https://", "").split("/")
        host = endpoint_parts[0]
        uri = f"/{'/'.join(endpoint_parts[1:])}"
        algorithm = 'AWS4-HMAC-SHA256'
        service = "execute-api"

        session = boto3.Session(profile_name=profile)
        credentials = session.get_credentials()

        access_key = credentials.access_key
        secret_key = credentials.secret_key
        now = datetime.datetime.utcnow()
        amz_date = now.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = now.strftime('%Y%m%d')
        content_type = "application/json"

        signed_headers = "content-type;host;x-amz-date"
        payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
        canonical_querystring = ""
        canonical_headers = 'content-type:' + content_type + '\n' + 'host:' + host + '\n' + 'x-amz-date:' + amz_date + '\n'
        canonical_request = method + '\n' + uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

        credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
        string_to_sign = algorithm + '\n' + amz_date + '\n' + credential_scope + '\n' + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        signing_key = self.__get_signature_key(secret_key, date_stamp, region, service)
        signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

        authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

        headers["content-type"] = content_type
        headers["x-amz-date"] = amz_date
        headers["Authorization"] = authorization_header

        return headers

    def execute(self, config, args, host=None):
        """
        Execute the specified REST request

        Based on the command that was passed to the Skelebot CLI (in args) the associated request
        is executed after populating all of the given variables with the values provided (or
        default values).

        If the response code from the request is 400 or above, an error message is printed and the
        CLI exits with a non-zero status code.

        Parameters
        ----------
        config : dict
            The configuration details for the Skelebot project
        args : argparse.Namespace
            The arguments passed through the CLI that correspond to the variables in the request
        host : str (optional)
            An alternate host on which to execute the requests (NOT IN USE)
        """

        req = self.requests[args.job]
        endpoint = req.endpoint
        method = req.method
        params = str(req.get_params_dict())
        headers = str(req.get_headers_dict())
        body = str(req.body)
        aws = req.aws

        # Populate Variables from Command Arguments
        for var in req.variables:
            var_key = f"{{{var.name}}}" if (var.default is None) else f"{{{var.name}:{var.default}}}"
            var_value = vars(args)[var.get_clean_name()]
            if (var.location == RestRequest.RestVar.Location.ENDPOINT):
                endpoint = endpoint.replace(var_key, var_value)
            elif (var.location == RestRequest.RestVar.Location.PARAMS):
                params = params.replace(var_key, var_value)
            elif (var.location == RestRequest.RestVar.Location.HEADERS):
                headers = headers.replace(var_key, var_value)
            elif (var.location == RestRequest.RestVar.Location.BODY):
                body = body.replace(var_key, var_value)

        body = self.__clean_body(body)
        params = json.loads(params.replace("'", "\""))
        headers = json.loads(headers.replace("'", "\""))

        if (aws == True):
            print("USING AWS AUTH")
            profile = req.awsProfile
            region = req.awsRegion
            headers = self.__get_aws_headers(endpoint, profile, region, method, body, params, headers)

        self.__show_execution(method, endpoint, params, headers, body)
        if (method == "GET"):
            response = request_api.get(endpoint, params=params, headers=headers)
        elif (method == "POST"):
            response = request_api.post(endpoint, data=body, params=params, headers=headers)
        elif (method == "PUT"):
            response = request_api.put(endpoint, data=body, params=params, headers=headers)
        elif (method == "DELETE"):
            response = request_api.delete(endpoint, params=params, headers=headers)

        if (response.ok):
            self.__display(f"SUCCESS: {response.status_code}:\n{response.content}")
            if response.text is not None:
                self.__display(response.text)
        else:
            self.__display(f"ERROR: {response.status_code}:\n{response.content}")
            exit(1)

    @classmethod
    def load(cls, config):
        """
        Instantiate the class based on a configuration Dictionary

        Parameters
        ----------
        config : dict
            A Dictionary containing the list of request objects used to instantiate the class

        Returns
        -------
        skelerest : Skelerest
            A Skelerest component object configured with the requests from the config dict
        """

        cls.validate(config)
        values = {}
        for attr, value in config.items():
            if (attr == "requests"):
                values[attr] = RestRequest.loadList(value)

        return cls(**values)
