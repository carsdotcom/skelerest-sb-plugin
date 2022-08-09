import re
import json
from enum import Enum
from schema import Schema, And, Or, Optional
from skelebot.objects.skeleYaml import SkeleYaml
from .rest_tuple import RestTuple

VARIABLE_REGEX = "{[a-zA-Z]+:?[^}]+?}"

class RestRequest(SkeleYaml):
    """ Holds the information required for a single pre-configured REST request """

    class RestVar:
        """ Holds the information for variables inside the RestRequest """

        name = None
        default = None
        location = None

        class Location(Enum):
            """ Enum for the different variable locations in the RestRequest """
            ENDPOINT = 1
            PARAMS = 2
            HEADERS = 3
            BODY = 4

        def __init__(self, name, default, location):
            """
            Initialize the RestVar with a name, default value, and it's location in the
            RestRequest object

            Parameters
            ----------
            name : str
                The name of the variable
            default : str
                The default value of the variable
            location : RestRequest.RestVar.Location
                The Location of the variable inside the RestRequest class
            """

            self.name = name
            self.default = default
            self.location = location

        def get_clean_name(self):
            """ Get the name value as used in ArgParser (dashes converted to underscores)"""
            return self.name.replace("-", "_")

    schema = Schema({
        'name': And(str, error='SkeleRequest \'name\' must be a String'),
        'endpoint': And(str, error='SkeleRequest \'endpoint\' must be a String'),
        'method': And(str, error='SkeleRequest \'method\' must be a String'), #TODO: Should add CRUD level content validation (POST/PUT contains body, method name is one of the four, etc.)
        Optional('params'): And(list, error='SkeleRequest \'params\' must be a list'),
        Optional('headers'): And(list, error='SkeleRequest \'headers\' must be a list'),
        Optional('body'): Or(dict, str, error='SkeleRequest \'body\' must be a Dictionary or String'),
        Optional('aws'): And(bool, error='SkeleRequest \'aws\' must be a boolean'),
        Optional('awsProfile'): And(str, error='SkeleRequest \'awsProfile\' must be a String'),
        Optional('awsRegion'): And(str, error='SkeleRequest \'awsRegion\' must be a String')
    }, ignore_extra_keys=True)

    name = None
    endpoint = None
    method = None
    params = None
    headers = None
    body = None
    variables = None
    aws = None
    awsProfile = None
    awsRegion = None

    def __init__(self, name, endpoint, method, params=None, headers=None, body=None, aws=False,
                 awsProfile=None, awsRegion="us-east-1"):
        """
        Initialize the RestRequest with all necessary and optional details

        In addition to setting the provided values, this initialize function also scans the
        endpoint, the params, the headers, and the body contents for variables that can be parsed
        out and provided via the Skelebot CLI.

        Parameters
        ----------
        name : str
            The name of the request to be used in the Skelebot CLI
        endpoint : str
            The http URI endpoint through which the API can be accessed
        method : str
            The REST method used in the API request (GET, POST, PUT, or DELETE)
        params : list (optional)
            A list of the query parameters used in the REST request
        headers : list (optional)
            A list of the header parameters used in the REST request
        body : dict or str (optional)
            A Dictionary representing the POST/PUT body of the request or a string with the path to
            the JSON request body file
            TODO
        """

        self.name = name
        self.endpoint = endpoint
        self.method = method
        self.params = params
        self.headers = headers
        self.aws = aws
        self.awsProfile = awsProfile
        self.awsRegion = awsRegion
        self.__load_body(body)
        self.__scan_variables(self.endpoint, RestRequest.RestVar.Location.ENDPOINT)
        self.__scan_variables(self.params, RestRequest.RestVar.Location.PARAMS)
        self.__scan_variables(self.headers, RestRequest.RestVar.Location.HEADERS)
        self.__scan_variables(self.body, RestRequest.RestVar.Location.BODY)

    def __load_body(self, body):
        """
        Load the request body from a file if it is not a Dictionary

        Pamaeters
        ---------
        body : dict or str
            If provided as a string the JSON file is loaded as the body, otherwise the dict is used
            directly
        """

        if (type(body) is str):
            with open(body) as body_file:
                body = json.load(body_file)

        self.body = body

    def __scan_variables(self, content, location):
        """
        Scan specific content in the request for variables provided in the configuration

        If a list is provided, the list is flattened into a string of the contents prior to the
        scanning process. Once the content is ready all of the variables are located by searching
        for curly braces such as `{var_name:default_value}`. Once the variables are located the
        names and default values (if provided as default values are optional) are parsed out and
        RestVar objects are created for each variable with the given location. These variables are
        then appended to the variables list in the class itself.

        Parameters
        ----------
        content : list or str
            The content that is being scanned for potential variables
        location : RestRequest.RestVar.Location
            The content Location that is being scanned (ENDPOINT, PARAMS, HEADERS, BODY)
        """

        variables = [] if (self.variables is None) else self.variables
        if (content is not None):
            if (type(content) is list):
                content = [str(item) for item in content]

            var_list = re.findall(VARIABLE_REGEX, str(content))
            var_list = [var.replace("{", "") for var in var_list]
            var_list = [var.replace("}", "") for var in var_list]

            for var in var_list:
                var = var.split(":")
                name = var[0]
                default = var[1] if len(var) > 1 else None
                variables.append(RestRequest.RestVar(name, default, location))

        self.variables = variables

    def __get_dict(self, tuples):
        """
        Converts a list of RestTuples into a Dictionary

        Parameters
        ----------
        tuples : list<RestTuple>
            A list of RestTuples to be converted to a Dictionary

        Returns
        -------
        params_dict : dict
            The Dictionary representation of the provided RestTuple list
        """

        params_dict = {}
        if (tuples is not None):
            for tup in tuples:
                params_dict[tup.name] = tup.value
        return params_dict

    def get_params_dict(self):
        """
        Returns the query parameters as a Dictionary object

        Returns
        -------
        params_dict : dict
            The Dictionary representation of the query parameters
        """

        return self.__get_dict(self.params)

    def get_headers_dict(self):
        """
        Returns the header parameters as a Dictionary object

        Returns
        -------
        headers_dict : dict
            The Dictionary representation of the header parameters
        """

        return self.__get_dict(self.headers)

    @classmethod
    def load(cls, config):
        """
        Load the class from values provided in a Dictionary config

        Parameters
        ----------
        config : dict
            Dictionary of values used to initialize the class

        Returns
        -------
        restRequest : RestRequest
            The class object initialized with values from the config Dictionary
        """

        cls.validate(config)
        values = {}
        for attr, value in config.items():
            if (attr == "params" or attr == "headers"):
                values[attr] = RestTuple.loadList(value)
            else:
                values[attr] = value

        return cls(**values)
