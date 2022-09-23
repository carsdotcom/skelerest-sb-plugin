import json
import ast
import boto3
import requests as request_api
from schema import Schema, And, Optional
from skelebot.objects.component import Activation, Component
from skelebot.objects.skeleYaml import SkeleYaml
from .rest_request import RestRequest
from .aws_auth import add_aws_headers

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
        """
        Clean the body of the request for use in JSON payloads

        Parameters
        ----------
        body : str
            The string representation of the request body

        Returns
        -------
        clean : str
            The clean version of the request body ready for use in a request
        """

        clean = body
        clean = clean.replace("'", "\"")
        clean = clean.replace("True", "true")
        clean = clean.replace("False", "false")
        return clean


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
        body = str(req.body_content)
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
            headers = add_aws_headers(endpoint, profile, region, method, params, headers, body=body)

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

    def toDict(self):
        cmds = self.commands
        self.commands = None
        dct = super().toDict()
        self.commands = cmds
        return dct

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
