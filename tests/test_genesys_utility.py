import pytest
import os
import json
import requests
import pandas as pd
from unittest.mock import patch, MagicMock

#
# ---------------- 1) TEST auth.py (get_genesys_access_token) ----------------
#
@patch("src.utility_functions.genesys_utility.auth.requests.post")
@patch("src.utility_functions.genesys_utility.auth._update_env_file")
def test_get_genesys_access_token_success(mock_update_env_file, mock_requests_post):
    """
    If the request is successful (status_code=200),
    we set genesys.configuration.access_token and update the .env file.
    """
    from src.utility_functions.genesys_utility.auth import get_genesys_access_token
    import PureCloudPlatformClientV2 as genesys
    
    # 1) Mock the POST response
    mock_requests_post.return_value.status_code = 200
    mock_requests_post.return_value.json.return_value = {"access_token": "FAKE_TOKEN_123"}

    # 2) Call the function
    get_genesys_access_token("CLIENT_ID", "CLIENT_SECRET", "mypurecloud.com")

    # 3) Check the results
    mock_requests_post.assert_called_once_with(
        "https://login.mypurecloud.com/oauth/token",
        data={"grant_type": "client_credentials"},
        headers={
            "Authorization": "Basic Q0xJRU5UX0lEOkNMSUVOVF9TRUNSRVQ=",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    # Confirm genesys.configuration.access_token is set
    assert genesys.configuration.access_token == "FAKE_TOKEN_123"
    mock_update_env_file.assert_called_once_with("GENESYS_ACCESS_TOKEN", "FAKE_TOKEN_123")


@patch("src.utility_functions.genesys_utility.auth.requests.post")
def test_get_genesys_access_token_error(mock_requests_post):
    """
    If the POST returns a non-200 status, the function should raise_for_status().
    """
    from src.utility_functions.genesys_utility.auth import get_genesys_access_token

    # Mock a 400 response
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    # This is the important part:
    # if we call mock_resp.raise_for_status(), it should raise an HTTPError
    mock_resp.raise_for_status.side_effect = requests.HTTPError("Simulated 400 error")

    mock_requests_post.return_value = mock_resp

    # Now we expect a requests.HTTPError when code calls response.raise_for_status()
    with pytest.raises(requests.HTTPError, match="Simulated 400 error"):
        get_genesys_access_token("CLIENT_ID", "CLIENT_SECRET", "mypurecloud.com")

    mock_requests_post.assert_called_once()

#
# ---------------- 2) TEST conversation_details_query.py ----------------
#

def test_build_post_analytics_conversations_details_query_payloads():
    from src.utility_functions.genesys_utility.conversation_details_query import (
        build_post_analytics_conversations_details_query_payloads
    )

    # Create a small DataFrame with conversation IDs
    df = pd.DataFrame({
        "conversationId": ["abc-123", None, "def-456", "admin", "xyz-789"]
    })

    # intervals
    intervals = [("2023-01-01", "2023-01-02"), ("2023-01-03", "2023-01-04")]
    payloads = build_post_analytics_conversations_details_query_payloads(
        df, "conversationId", intervals, chunk_size=2
    )
    
    # We expect each interval to produce chunked JSON. 
    # IDs are ["abc-123", "def-456", "admin", "xyz-789"], ignoring None => 4 valid strings
    # In chunks of 2 => chunk1=["abc-123","def-456"], chunk2=["admin","xyz-789"]
    # 2 intervals => total 4 payloads
    assert len(payloads) == 4
    for p in payloads:
        data = json.loads(p)
        assert "conversationFilters" in data
        conv_predicates = data["conversationFilters"][0]["predicates"]
        # Each chunk should have 2 conversation IDs
        assert len(conv_predicates) == 2

@patch("src.utility_functions.genesys_utility.conversation_details_query.fetch_all_pages_for_conversations_details_query_payload")
def test_fetch_post_analytics_conversations_details_query_df(mock_fetch_all_pages):
    from src.utility_functions.genesys_utility.conversation_details_query import (
        fetch_post_analytics_conversations_details_query_df
    )
    # Mock return of one DataFrame per payload
    fake_df1 = pd.DataFrame([{"col": 1}])
    fake_df2 = pd.DataFrame([{"col": 2}])
    mock_fetch_all_pages.side_effect = [fake_df1, fake_df2]

    # Build a sample DataFrame with conversation IDs
    df_in = pd.DataFrame({"conv": ["123", "456", "789"]})
    intervals = [("2023-01-01", "2023-01-02")]

    api_client = MagicMock()
    result_df = fetch_post_analytics_conversations_details_query_df(api_client, intervals, df_in, "conv")

    # We expect two calls => chunking by 10 IDs => we only have 3, so just 1 chunk * 1 interval => 1 call?
    # However, we patch the entire loop, let's assume chunk size=10 => 1 chunk => 1 payload => 1 DataFrame
    # Actually, if chunk_size=10 is default, we only have 1 chunk => 1 payload => so we might expect 1 return
    # But let's see the code: chunk_size=10 => 1 chunk, intervals=1 => 1 payload => so only 1 DataFrame.
    # But we forced side_effect with 2 DataFrames, so let's see how many payloads it builds

    # The function uses chunk_size=10 by default => 3 IDs => 1 chunk => 1 interval => total 1 payload => 1 returned DF
    # That means only 1 side_effect is used. The second won't be used.
    # Let's confirm:
    assert len(result_df) == 1
    assert result_df["col"].iloc[0] == 1
    mock_fetch_all_pages.assert_called_once()


#
# ---------------- 3) TEST conversation.py + users.py (basic setup) ----------------
#
@patch("src.utility_functions.genesys_utility.conversation.genesys.api_client.ApiClient")
def test_genesys_conversation_setup(mock_ApiClient):
    from src.utility_functions.genesys_utility.conversation import genesys_conversation_setup
    import PureCloudPlatformClientV2 as genesys

    mock_client = MagicMock()
    mock_client.access_token = "FAKE_CONV_TOKEN"
    mock_ApiClient.return_value.get_client_credentials_token.return_value = mock_client

    api_instance = genesys_conversation_setup("ID123", "SEC456")

    # Confirm the region host was set
    assert genesys.configuration.host == genesys.PureCloudRegionHosts.us_east_2.get_api_host()
    # Confirm the access_token is set
    assert genesys.configuration.access_token == "FAKE_CONV_TOKEN"

    # Check the type WITHOUT importing from .rest
    assert isinstance(api_instance, genesys.ConversationsApi)


@patch("src.utility_functions.genesys_utility.users.genesys.api_client.ApiClient")
def test_genesys_users_setup(mock_ApiClient):
    """
    Ensure users setup sets region host and obtains token, returning a UsersApi instance.
    """
    from src.utility_functions.genesys_utility.users import genesys_users_setup
    import PureCloudPlatformClientV2 as genesys

    mock_client = MagicMock()
    mock_client.access_token = "FAKE_USERS_TOKEN"
    mock_ApiClient.return_value.get_client_credentials_token.return_value = mock_client

    api_instance = genesys_users_setup("ID999", "SEC999")
    assert genesys.configuration.host == genesys.PureCloudRegionHosts.us_east_2.get_api_host()
    assert genesys.configuration.access_token == "FAKE_USERS_TOKEN"
    assert api_instance.__class__.__name__ == "UsersApi"


#
# ---------------- 4) TEST transformations.py (clean_genesys_id_column) ----------------
#
def test_clean_genesys_id_column():
    from src.utility_functions.genesys_utility.transformations import clean_genesys_id_column

    df = pd.DataFrame({
        "conversation_id": [
            "/some/path/abc-1234",    # has prefix
            "Pending",                # should remove row
            "/ignore/def-4567-9",     # not a valid UUID pattern
            "admin",                  # remove row
            "00000000-0000-0000-0000-000000000000",  # valid UUID
            None,  # NaN
            "11111111-1111-1111-1111-111111111111"   # valid
        ]
    })

    cleaned_df = clean_genesys_id_column(df, "conversation_id")
    # Expect we keep only rows that match a full UUID pattern
    # The first row => "abc-1234" is not a 36-char UUID => removed
    # "Pending" => removed
    # "def-4567-9" => not valid => removed
    # "admin" => removed
    # So we keep:
    # "00000000-0000-0000-0000-000000000000"
    # "11111111-1111-1111-1111-111111111111"

    assert len(cleaned_df) == 2
    assert cleaned_df["conversation_id"].tolist() == [
        "00000000-0000-0000-0000-000000000000",
        "11111111-1111-1111-1111-111111111111"
    ]
