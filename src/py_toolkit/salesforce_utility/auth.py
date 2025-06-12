import os
import requests
import warnings
from dotenv import load_dotenv
from .common import _get_env_path, _update_env_file

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*setDaemon.*"
)

def get_salesforce_refresh_token(authorization_code: str) -> str:
    """
    Exchanges an authorization code for a refresh token and updates the .env file accordingly.
    """
    load_dotenv(dotenv_path=_get_env_path())

    client_id = os.getenv("SF_KEY")
    client_secret = os.getenv("SF_SECRET")
    if not client_id or not client_secret:
        raise ValueError("SF_KEY or SF_SECRET is missing from your .env file.")

    callback_url = "https://localhost/"

    # 1) Exchange authorization code for refresh token
    access_token_url = (
        "https://login.salesforce.com/services/oauth2/token?"
        f"grant_type=authorization_code"
        f"&code={authorization_code}"
        f"&client_id={client_id}"
        f"&client_secret={client_secret}"
        f"&redirect_uri={callback_url}"
    )
    resp = requests.post(access_token_url)
    resp_json = resp.json()

    if "refresh_token" not in resp_json:
        raise ValueError(f"Could not retrieve 'refresh_token' from:\n{resp_json}")

    # 2) Use the newly obtained refresh token to get an access token
    refresh_token_value = resp_json["refresh_token"]
    refresh_token_url = (
        "https://login.salesforce.com/services/oauth2/token"
        f"?grant_type=refresh_token"
        f"&client_id={client_id}"
        f"&client_secret={client_secret}"
        f"&refresh_token={refresh_token_value}"
    )
    refresh_resp = requests.post(refresh_token_url)
    refresh_resp.raise_for_status()
    refresh_json = refresh_resp.json()
    new_access_token = refresh_json.get("access_token")

    if not new_access_token:
        raise ValueError(f"No 'access_token' field in refresh token response:\n{refresh_json}")

    # 3) Update .env with the new token
    _update_env_file("SF_REFRESH", new_access_token)

    print(f"Successfully retrieved a new refresh token:\n{new_access_token}")
    return new_access_token


def print_salesforce_authorize_url():
    """
    Prints the Salesforce authorization URL where the user must visit
    to grant this application permission, returning an authorization code.
    """
    load_dotenv(dotenv_path=_get_env_path())
    client_id = os.getenv("SF_KEY")
    if not client_id:
        raise ValueError("SF_KEY is missing from your .env file.")

    callback_url = "https://localhost/"
    auth_code_url = (
        "https://login.salesforce.com/services/oauth2/authorize?"
        f"client_id={client_id}&redirect_uri={callback_url}&response_type=code"
    )

    print("Please visit this URL to authorize the application:\n")
    print(auth_code_url)
    print(
        "\nAfter allowing access, you'll be redirected to a URL containing 'code='. "
        "Use that code to obtain and store the refresh token.\n"
    )


