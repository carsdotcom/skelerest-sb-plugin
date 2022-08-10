import sys
import os
import base64
import datetime
import hashlib
import hmac
import boto3

ALGORITHM = "AWS4-HMAC-SHA256"
CONTENT_TYPE = "application/json"
SERVICE = "execute-api"

def sign(key, string):
    """
    Perform Signing via hmac and hashlib

    Parameters
    ----------
    key : str
        The secret key for the hashing function
    string : str
        The string to be encoded and hashed for signing

    Returns
    -------
    signed : str
        The signed version of the string value
    """

    signed = hmac.new(key, string.encode("utf-8"), hashlib.sha256)
    return signed

def hash(string):
    """
    Perform Hashing hashlib

    Parameters
    ----------
    string : str
        The string value to be hashed

    Returns
    -------
    hashed : str
        The hashed version of the string value
    """

    hashed = hashlib.sha256(string.encode('utf-8')).hexdigest()
    return hashed

def get_signature_key(key, date_stamp, region):
    """
    Generate the signature key for the AWS Auth.

    Parameters
    ----------
    key : str
        The secret key for Auth
    date_stamp : str
        The current date (Year, Month, Day)
    region : str
        The name of the AWS region to be used for Auth

    Returns
    -------
    signed_key : str
        The signed key for AWS service Auth
    """

    date_key = sign(('AWS4' + key).encode('utf-8'), date_stamp).digest()
    region_key = sign(date_key, region).digest()
    service_key = sign(region_key, SERVICE).digest()
    signed_key = sign(service_key, 'aws4_request').digest()
    return signed_key

# TODO: MOCK
def get_credentials(profile):
    """
    Creates a session based on the given profile name and obtains the Auth credentials.

    Parameters
    ----------
    profile : str
        The name of the AWS profile to be used for Auth

    Returns
    -------
    credentials : botocore.credentials.Credentials
        The AWS credentials object from which the access key and secret key can be obtained
    """

    session = boto3.Session(profile_name=profile)
    return session.get_credentials()

def split_endpoint(endpoint):
    """
    Split the endpoint into the host string and the uri string

    Parameters
    ----------
    endpoint : str
        The full URL of the API that is being called with the request

    Returns
    -------
    host : str
        The name of the host taken from the endpoint URL
    uri : str
        The API path taken from the endpoint URL
    """

    endpoint_parts = endpoint.replace("https://", "").split("/")
    host = endpoint_parts[0]
    uri = f"/{'/'.join(endpoint_parts[1:])}"
    return host, uri

def add_aws_headers(endpoint, profile, region, method, params, headers, body=""):
    """
    Add AWS Auth headers needed for making requests against AWS APIs

    Parameters
    ----------
    endpoint : str
        The full URL of the API that is being called with the request
    profile : str
        The name of the AWS profile to be used for Auth
    region : str
        The name of the AWS region to be used for Auth
    method : str
        The name of the HTTP method to be used in the request
    params : dict
        TODO The dict of query parameters for the request
    headers : dict
        The dict of header parameters for the request
    body : str (optional)
        The string representation of the request body

    Returns
    -------
    headers : dict
        The dict of header parameters for the request with the addition of AWS Authorization
    """

    # Obtain Credentials from AWS Profile
    credentials = get_credentials(profile)
    access_key = credentials.access_key
    secret_key = credentials.secret_key

    # Generate Current Date Strings
    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    # Build the Authorization Header for AWS Requests
    host, uri = split_endpoint(endpoint)
    signed_headers = "content-type;host;x-amz-date"
    payload_hash = hash(body)
    signing_key = get_signature_key(secret_key, date_stamp, region)
    canonical_querystring = ""
    canonical_headers = f"content-type:{CONTENT_TYPE}\nhost:{host}\nx-amz-date:{amz_date}\n"
    canonical_request = f"{method}\n{uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    credential_scope = f"{date_stamp}/{region}/{SERVICE}/aws4_request"
    string_to_sign = f"{ALGORITHM}\n{amz_date}\n{credential_scope}\n{hash(canonical_request)}"
    signature = sign(signing_key, (string_to_sign)).hexdigest()
    authorization_header = f"{ALGORITHM} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

    # Add the necessary AWS Auth Headers
    headers["content-type"] = CONTENT_TYPE
    headers["x-amz-date"] = amz_date
    headers["Authorization"] = authorization_header

    return headers
