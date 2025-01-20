import os
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext

def get_client_context(base_url, site_path, username, password):
    """
    Acquires a token and returns a ClientContext for the specified SharePoint site.
    """
    # Gracefully handle trailing slash
    base_url = base_url.rstrip("/")
    site_url = base_url + site_path

    ctx_auth = AuthenticationContext(site_url)
    ctx_auth.acquire_token_for_user(username=username, password=password)
    return ClientContext(site_url, ctx_auth)
