from schema import Schema, And
from skelebot.objects.skeleYaml import SkeleYaml

class RestTuple(SkeleYaml):
    """ Holds the information for name value pairs for REST requests (query/header parameters) """
    
    schema = Schema({
        'name': And(str, error='SkeleRequestTuple \'name\' must be a String'),
        'value': And(str, error='SkeleRequestTuple \'value\' must be a String')
    }, ignore_extra_keys=True)

    name = None
    value = None

    def __init__(self, name, value):
        """
        Initialize the RestTuple with a name and value

        Parameters
        ----------
        name : str
            The name of the pair
        value : str
            The value of the pair
        """

        self.name = name
        self.value = value

    def __str__(self):
        """ Overwrite the __str__ method to create a simple string representation of the tuple """
        return f"{self.name} {self.value}"
