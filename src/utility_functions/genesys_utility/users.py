import PureCloudPlatformClientV2 as genesys

def genesys_users_setup(client_id, client_secret):
    """
    Sets up and returns a Genesys UsersApi instance, 
    pre-configured with credentials.
    """
    region = genesys.PureCloudRegionHosts.us_east_2
    genesys.configuration.host = region.get_api_host()
    apiclient = genesys.api_client.ApiClient().get_client_credentials_token(client_id, client_secret)
    genesys.configuration.access_token = apiclient.access_token
    api_instance = genesys.UsersApi()
    return api_instance

