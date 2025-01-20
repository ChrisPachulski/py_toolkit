import os
import base64
import requests
import PureCloudPlatformClientV2 as genesys
from .common import _update_env_file

def get_genesys_access_token(client_id, client_secret, environment):
    """
    Fetches a new access token from Genesys PureCloud API and updates genesys.configuration.
    Also writes the token to .env for later usage.
    """
    authorization = base64.b64encode(
        bytes(client_id + ":" + client_secret, "ISO-8859-1")
    ).decode("ascii")

    request_headers = {
        "Authorization": f"Basic {authorization}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    request_body = {
        "grant_type": "client_credentials"
    }

    response = requests.post(
        f"https://login.{environment}/oauth/token",
        data=request_body,
        headers=request_headers
    )
    
    if response.status_code == 200:
        access_token = response.json().get("access_token")
        genesys.configuration.access_token = access_token
        _update_env_file("GENESYS_ACCESS_TOKEN", access_token)
    else:
        response.raise_for_status()
