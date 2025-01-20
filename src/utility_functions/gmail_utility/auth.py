import os
from token import STRING
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from .common import _get_env_path

def build_gmail_service(
    scopes=['https://www.googleapis.com/auth/gmail.modify']
):
    """
    Builds an authenticated Gmail service using OAuth2 credentials.

    Returns:
        service: A Gmail API service instance.
    """
    load_dotenv(dotenv_path=_get_env_path())
    
    client_secret_file=os.getenv('GOOGLE_OAUTH_PATH')
    token_file=os.getenv('GOOGLE_OAUTH_REFRESH_PATH')
        
    creds = None

    # Load existing credentials if they exist
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    # If no creds or invalid, do the OAuth2 flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
            creds = flow.run_local_server(port=8081,prompt='consent',access_type='offline')

        # Save the creds for next time
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    # Build the Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service
