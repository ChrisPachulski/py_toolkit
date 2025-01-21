import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

# Adjust imports to match your package structure
from src.utility_functions.google_sheets_utility.sheets import create_or_update_google_sheet, auto_resize_columns

@pytest.fixture
def mock_spread():
    """
    Return a MagicMock to represent gspread_pandas.Spread object.
    We'll patch Spread(...) so it returns this mock in your code.
    """
    spread_mock = MagicMock()
    # e.g., configure default return values for methods if needed
    spread_mock.find_sheet.return_value = None  # as if the sheet doesn't exist
    spread_mock.spread.title = "Mock Workbook"
    spread_mock.url = "https://docs.google.com/spreadsheets/d/FAKE_ID"
    
    # If you need deeper nested mocks:
    # spread_mock.client.open.return_value = ...
    return spread_mock


@pytest.fixture
def mock_service_account():
    """
    Return a MagicMock to represent gspread.service_account(...) result.
    We'll patch gspread.service_account so it returns this mock.
    """
    service_mock = MagicMock()
    # e.g. configure create(...) method to return a fake "sh" object
    fake_sh = MagicMock()
    fake_sh.id = "FAKE_SHEET_ID"
    service_mock.create.return_value = fake_sh
    return service_mock


@patch("src.utility_functions.google_sheets_utility.sheets.gs.service_account")
@patch("src.utility_functions.google_sheets_utility.sheets.Spread")
def test_create_new_workbook(
    mock_spread_cls,
    mock_service_account_cls,
    mock_spread,
    mock_service_account,
):
    """
    Test scenario where the workbook does NOT exist in Google Drive, so an exception
    is raised by Spread(...) in your code, and then a new workbook is created.
    """
    # 1) We want the first call to Spread(...) to raise an Exception so that 
    #    your code goes into the "except" block.
    mock_spread_cls.side_effect = [Exception("Workbook not found"), mock_spread]

    # 2) Patch gspread.service_account to return our mock
    mock_service_account_cls.return_value = mock_service_account

    # 3) Call your function
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    create_or_update_google_sheet(
        share_with="test@example.com",
        df=df,
        workbook_name="NonExistentWorkbook",
        sheet_name="MySheet",
        interactive=False,
        service_account_path="fake_path.json",
    )

    # 4) Validate that your logic attempted to create the new workbook
    mock_service_account.create.assert_called_once_with("NonExistentWorkbook")
    # Then presumably you call Spread(...) again with the same name:
    assert mock_spread_cls.call_count == 2
    # (first time raises exception, second time returns mock_spread)

    # 5) Check that the DataFrame was written
    mock_spread.df_to_sheet.assert_called_once()
    # Possibly more specific asserts, e.g. which arguments were used:
    (args, kwargs) = mock_spread.df_to_sheet.call_args
    assert kwargs["sheet"] == "MySheet"
    assert kwargs["freeze_headers"] is True
    # etc.


@patch("src.utility_functions.google_sheets_utility.sheets.gs.service_account")
@patch("src.utility_functions.google_sheets_utility.sheets.Spread")
def test_update_existing_sheet(
    mock_spread_cls,
    mock_service_account_cls,
    mock_spread,
    mock_service_account
):
    """
    Test scenario where the workbook exists AND the sheet also exists,
    and interactive=False means we skip the overwrite prompt and just overwrite.
    """
    # 1) We do NOT want an exception from Spread this time
    mock_spread_cls.return_value = mock_spread
    mock_service_account_cls.return_value = mock_service_account
    
    # 2) Fake that the sheet DOES exist
    mock_spread.find_sheet.return_value = True

    # 3) Call your function
    df = pd.DataFrame({"C": [10, 20], "D": [30, 40]})
    create_or_update_google_sheet(
        share_with="test@example.com",
        df=df,
        workbook_name="ExistingWorkbook",
        sheet_name="ExistingSheet",
        interactive=False,
        service_account_path="fake_path.json",
    )

    # 4) Because the sheet does exist, code sees interactive=False => 
    #    "Interactive Sheet Overwrite Logic has been declined" path
    #    => calls clear_sheet(1, 1, sheet_name), then df_to_sheet(...)
    mock_spread.clear_sheet.assert_called_once_with(1, 1, "ExistingSheet")
    mock_spread.df_to_sheet.assert_called_once()
    # Also verify no new workbook creation
    mock_service_account.create.assert_not_called()


@patch("src.utility_functions.google_sheets_utility.sheets.service_account.Credentials")
@patch("src.utility_functions.google_sheets_utility.sheets.build")
def test_auto_resize_columns(mock_build, mock_credentials):
    from googleapiclient.discovery import Resource
    from src.utility_functions.google_sheets_utility.sheets import auto_resize_columns

    # Create a mock for the "sheets" resource
    mock_sheets_service = MagicMock()
    mock_sheets = MagicMock()
    
    # This line ensures calling .spreadsheets() returns our mock_sheets
    mock_sheets_service.spreadsheets.return_value = mock_sheets

    # Tell build(...) to return the top-level service
    mock_build.return_value = mock_sheets_service

    # Now configure your .get() -> .execute() chain
    # The code calls get() at least twice, so you can do side_effect or configure in sequence:
    mock_sheets.get.return_value.execute.side_effect = [
        {
            # First get() call returns the sheet metadata with "MySheet"
            "sheets": [
                {
                    "properties": {
                        "title": "MySheet",
                        "sheetId": 12345,
                        "gridProperties": {"columnCount": 3}
                    }
                }
            ]
        },
        {
            # Second get() call for columnMetadata
            "sheets": [
                {
                    "data": [
                        {
                            "columnMetadata": [
                                {"pixelSize": 100}, {"pixelSize": 80}, {}
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    # Now call the function
    result = auto_resize_columns(
        spreadsheet_id="FAKE_SPREADSHEET_ID",
        sheet_name="MySheet",
        service_account_path="fake_path.json"
    )
    assert result == "Columns auto-resized successfully."

    # We expect multiple batchUpdate calls (one for the autoResizeDimensions,
    # then another for each column in the final loop).
    assert mock_sheets.batchUpdate.call_count == 1 + 3
    

