import pytest
import pandas as pd
from unittest.mock import MagicMock

@pytest.fixture
def mock_service(mocker):
    """
    Create a MagicMock representing the Gmail service, then patch
    'auth.build_gmail_service' so 'send.py' uses our mock.
    """
    mock_service = MagicMock()
    # Patch the function in the 'auth' module, since your code calls auth.build_gmail_service()
    mocker.patch(
        "src.utility_functions.gmail_utility.auth.build_gmail_service",
        return_value=mock_service
    )

    # Make the chain of calls return a predictable message ID
    mock_service.users().messages().send().execute.return_value = {"id": "MOCK_MESSAGE_ID"}
    return mock_service


def test_send_email_with_dataframe(mock_service):
    """
    Sends an email where `data` is a Pandas DataFrame.
    """
    # IMPORTANT: import after patching
    from src.utility_functions.gmail_utility.send import gmail_send_message

    df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    result = gmail_send_message(
        data=df,
        receivers="test@example.com",
        file_titles="test_data.csv",
        subject="Test Subject",
        content="Here is some test content."
    )
    assert result is not None
    assert result["id"] == "MOCK_MESSAGE_ID"


def test_send_email_with_file_path(tmp_path, mock_service):
    """
    Sends an email where `data` is a file path.
    """
    from src.utility_functions.gmail_utility.send import gmail_send_message

    # Create a temporary file
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Hello, this is a test file.")

    result = gmail_send_message(
        data=str(test_file),
        receivers="test@example.com",
        file_titles="sample.txt",
        subject="File Attachment Test",
        content="Please see attached file."
    )
    assert result is not None
    assert result["id"] == "MOCK_MESSAGE_ID"


def test_send_email_mismatched_lists(mock_service):
    """
    If data and file_titles lengths differ, send function returns None.
    """
    from src.utility_functions.gmail_utility.send import gmail_send_message

    # 2 data items vs 1 file title => mismatch
    result = gmail_send_message(
        data=["data.csv", "data2.csv"],
        file_titles="one_title.csv",
        receivers="test@example.com",
        subject="Mismatch Test",
        content="This should fail because data and file_titles lengths don't match."
    )
    assert result is None


def test_send_email_invalid_data_type(mock_service):
    """
    If data is an unsupported type, the code catches ValueError and returns None.
    """
    from src.utility_functions.gmail_utility.send import gmail_send_message

    class NotSupported:
        pass

    # 'create_attachments' raises ValueError => `send.py` catches it and returns None
    result = gmail_send_message(
        data=NotSupported(),
        file_titles="invalid.dat",
        receivers="test@example.com",
        subject="Invalid Data Test",
        content="Should trigger an exception."
    )
    assert result is None
