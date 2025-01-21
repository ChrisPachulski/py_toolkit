import pytest
import os
from unittest.mock import MagicMock, patch
import requests
import pandas as pd

#
# ==================== 1) TEST auth.py ====================
#
@patch("src.utility_functions.salesforce_utility.auth.requests.post")
@patch("src.utility_functions.salesforce_utility.auth._update_env_file")
@patch("src.utility_functions.salesforce_utility.auth.load_dotenv")
def test_get_salesforce_refresh_token(
    mock_load_dotenv,
    mock_update_env_file,
    mock_requests_post
):
    """
    Test that get_salesforce_refresh_token makes the correct requests, 
    updates .env, and returns the new token.
    """
    from src.utility_functions.salesforce_utility.auth import get_salesforce_refresh_token

    # 1. Mock environment variables
    with patch.dict(os.environ, {"SF_KEY": "FakeKey", "SF_SECRET": "FakeSecret"}, clear=True):
        # 2. First POST (code -> refresh token)
        #    We'll simulate a JSON response that includes a refresh_token
        mock_requests_post.side_effect = [
            MagicMock(json=lambda: {"refresh_token": "FAKE_REFRESH_TOKEN"}),
            MagicMock(json=lambda: {"access_token": "NEW_ACCESS_TOKEN"})
        ]

        new_token = get_salesforce_refresh_token("AUTH_CODE_ABC123")
        assert new_token == "NEW_ACCESS_TOKEN"

        # Check that we updated the .env with SF_REFRESH
        mock_update_env_file.assert_called_once_with("SF_REFRESH", "NEW_ACCESS_TOKEN")

        # The first request
        first_call_url = mock_requests_post.call_args_list[0][0][0]
        assert "authorization_code" in first_call_url
        # The second request
        second_call_url = mock_requests_post.call_args_list[1][0][0]
        assert "refresh_token=FAKE_REFRESH_TOKEN" in second_call_url


@patch("src.utility_functions.salesforce_utility.auth.load_dotenv")
def test_print_salesforce_authorize_url(mock_load_dotenv, capsys):
    """
    Test that print_salesforce_authorize_url prints the correct URL.
    """
    from src.utility_functions.salesforce_utility.auth import print_salesforce_authorize_url

    with patch.dict(os.environ, {"SF_KEY": "FakeKey"}, clear=True):
        print_salesforce_authorize_url()
        captured = capsys.readouterr()
        assert "Please visit this URL to authorize the application:" in captured.out
        assert "login.salesforce.com/services/oauth2/authorize" in captured.out
        assert "client_id=FakeKey" in captured.out

#
# ==================== 2) TEST common.py ====================
#
@patch("src.utility_functions.salesforce_utility.common.os.path.exists", return_value=True)
def test_update_env_file(mock_exists, tmp_path):
    """
    Basic test to confirm _update_env_file writes or updates a key in .env.
    We use a temp file to simulate the .env path.
    """
    from src.utility_functions.salesforce_utility.common import _update_env_file, _get_env_path

    # Patch _get_env_path so it returns a path to a temp file
    env_file = tmp_path / ".env"
    with patch("src.utility_functions.salesforce_utility.common._get_env_path", return_value=str(env_file)):
        # Write a starter .env
        env_file.write_text("OLD_KEY=OLD_VALUE\n")

        _update_env_file("NEW_KEY", "NEW_VALUE")
        content = env_file.read_text()
        assert "OLD_KEY=OLD_VALUE" in content
        assert "NEW_KEY=NEW_VALUE" in content

        # Updating existing key
        _update_env_file("OLD_KEY", "UPDATED")
        content = env_file.read_text()
        assert "OLD_KEY=UPDATED" in content

#
# ==================== 3) TEST transformations.py ====================
#
def test_flatten_record():
    from src.utility_functions.salesforce_utility.transformations import flatten_record

    nested_record = {
        "Id": "001",
        "attributes": {"type": "Account", "url": "/Account/001"},
        "Name": "Test Account",
        "Owner": {
            "attributes": {"type": "User", "url": "/User/005"},
            "Id": "005",
            "Name": "Owner Name",
        },
    }

    flat = flatten_record(nested_record)
    # 'attributes' keys are skipped
    # Relationship (Owner) is flattened
    assert flat["Id"] == "001"
    assert "attributes" not in flat
    assert flat["Owner__Id"] == "005"
    assert flat["Owner__Name"] == "Owner Name"


def test_convert_to_eastern_time():
    from src.utility_functions.salesforce_utility.transformations import convert_to_eastern_time
    # Example UTC datetime string
    original_utc = "2023-06-01T12:00:00Z"
    converted = convert_to_eastern_time(original_utc)
    # Something like '2023-06-01 08:00:00 EDT' (depending on DST or date)
    # We'll just assert it has "2023-06-01" and "EDT" or "EST"
    assert "2023-06-01" in converted
    assert "EDT" in converted or "EST" in converted

#
# ==================== 4) TEST query.py ====================
#
@patch("src.utility_functions.salesforce_utility.query.requests.get")
@patch("src.utility_functions.salesforce_utility.query.load_dotenv")
def test_query_salesforce_soql(mock_load_dotenv, mock_requests_get):
    from src.utility_functions.salesforce_utility.query import query_salesforce_soql
    from src.utility_functions.salesforce_utility.transformations import convert_to_eastern_time

    # Mock environment: set SF_REFRESH
    with patch.dict(os.environ, {"SF_REFRESH": "FakeRefreshToken"}, clear=True):
        # Mock requests response
        def mock_json():
            return {
                "records": [
                    {
                        "Id": "001",
                        "Name": "Test Record",
                        "attributes": {"type": "Account"},
                        "CreatedDate": "2023-06-01T12:00:00Z",
                    }
                ]
            }

        mock_req = MagicMock()
        mock_req.json = mock_json
        mock_requests_get.return_value = mock_req

        df = query_salesforce_soql("SELECT Id, Name FROM Account")

        mock_requests_get.assert_called_once()
        # Check the shape or columns
        assert len(df) == 1
        assert "id" in df.columns
        assert "name" in df.columns
        # "created_date" was converted to eastern time
        assert "createddate" in df.columns
        # The date in row 0 should have EDT or EST appended
        assert "EDT" in df.loc[0, "createddate"] or "EST" in df.loc[0, "createddate"]

#
# ==================== 5) TEST reporting.py ====================
#
@patch("src.utility_functions.salesforce_utility.reporting.requests.get")
def test_query_salesforce_report(mock_requests_get):
    from src.utility_functions.salesforce_utility.reporting import query_salesforce_report
    # Mock environment
    with patch.dict(os.environ, {"SF_REFRESH": "FakeRefreshToken"}, clear=True):
        # We create a fake JSON that matches a typical Analytics report structure
        mock_report_json = {
            "reportMetadata": {
                "detailColumns": ["ACCOUNT.NAME", "ACCOUNT.CREATEDDATE"]
            },
            "reportExtendedMetadata": {
                "detailColumnInfo": {
                    "ACCOUNT.NAME": {"dataType": "string"},
                    "ACCOUNT.CREATEDDATE": {"dataType": "datetime"}
                }
            },
            "factMap": {
                "T!T": {
                    "rows": [
                        {
                            "dataCells": [
                                {"label": "Acme Corp", "value": "Acme Corp"},
                                {"label": "2023-06-01T12:00:00Z", "value": "2023-06-01T12:00:00Z"}
                            ]
                        },
                        {
                            "dataCells": [
                                {"label": "Test Inc", "value": "Test Inc"},
                                {"label": "2023-06-02T10:00:00Z", "value": "2023-06-02T10:00:00Z"}
                            ]
                        }
                    ]
                }
            }
        }

        mock_req = MagicMock()
        mock_req.status_code = 200
        mock_req.json.return_value = mock_report_json
        mock_requests_get.return_value = mock_req

        df = query_salesforce_report("FAKE_REPORT_ID")

        assert len(df) == 2
        assert "account_name" in df.columns
        assert "account_createddate" in df.columns
        # We expect them to be converted to eastern time strings
        # Let's just check for EDT or EST in the first row
        assert ("EDT" in df.loc[0, "account_createddate"]) or ("EST" in df.loc[0, "account_createddate"])

        # Confirm the request was made
        mock_requests_get.assert_called_once()
        url_called = mock_requests_get.call_args[0][0]
        assert "analytics/reports/FAKE_REPORT_ID" in url_called
