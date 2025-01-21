import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

#
# ----------------- 1. TEST auth.py (get_client_context) -----------------
#
@patch("src.utility_functions.sharepoint_utility.auth.AuthenticationContext")
@patch("src.utility_functions.sharepoint_utility.auth.ClientContext")
def test_get_client_context(mock_ClientContext, mock_AuthenticationContext):
    """
    Test that get_client_context constructs the correct site URL, 
    acquires token with username/password, and returns a ClientContext.
    """
    from src.utility_functions.sharepoint_utility.auth import get_client_context

    # Configure Mocks
    mock_auth_context = MagicMock()
    mock_AuthenticationContext.return_value = mock_auth_context

    mock_ctx = MagicMock()
    mock_ClientContext.return_value = mock_ctx

    # Call function
    result = get_client_context(
        base_url="https://my.sharepoint.com/",
        site_path="/sites/MySite",
        username="myuser@example.com",
        password="fakepassword"
    )

    # Assertions
    # => site_url = base_url.rstrip("/") + site_path = "https://my.sharepoint.com" + "/sites/MySite"
    mock_AuthenticationContext.assert_called_once_with("https://my.sharepoint.com/sites/MySite")
    mock_auth_context.acquire_token_for_user.assert_called_once_with(username="myuser@example.com", password="fakepassword")

    # ClientContext should be constructed with site_url + auth
    mock_ClientContext.assert_called_once_with("https://my.sharepoint.com/sites/MySite", mock_auth_context)
    assert result == mock_ctx  # Should return the mock ctx

#
# ----------------- 2. TEST common.py -----------------
#
@pytest.fixture
def mock_client_context():
    """
    A fixture returning a MagicMock that represents a SharePoint ClientContext.
    We'll attach sub-mocks for .web, .execute_query(), etc.
    """
    ctx = MagicMock()
    # common usage: ctx.load(...) -> ctx.execute_query()
    # We can define no-op or do side effects
    ctx.execute_query.return_value = None

    # Simulate ctx.web.lists -> a collection of lists
    mock_web = MagicMock()
    ctx.web = mock_web
    ctx.web.lists = []
    return ctx


def test_get_documents_library_found(mock_client_context):
    from src.utility_functions.sharepoint_utility.common import get_documents_library

    # Setup: let's say the web.lists has one "Documents" library
    mock_list = MagicMock()
    mock_list.properties = {"Title": "Documents", "BaseTemplate": 101}
    mock_client_context.web.lists = [mock_list]

    result = get_documents_library(mock_client_context, library_title="Documents")
    assert result == mock_list, "Should return the matching library list object"


def test_get_documents_library_not_found(mock_client_context):
    from src.utility_functions.sharepoint_utility.common import get_documents_library

    # No lists with correct name/base template
    mock_list = MagicMock()
    mock_list.properties = {"Title": "Wrong", "BaseTemplate": 101}
    mock_client_context.web.lists = [mock_list]

    result = get_documents_library(mock_client_context, library_title="Documents")
    assert result is None, "Should return None if not found"


def test_get_folder_by_server_relative_url(mock_client_context):
    from src.utility_functions.sharepoint_utility.common import get_folder_by_server_relative_url

    # Setup: mock the .web.get_folder_by_server_relative_url(...) call
    mock_folder = MagicMock()
    mock_client_context.web.get_folder_by_server_relative_url.return_value = mock_folder

    # Call
    folder = get_folder_by_server_relative_url(mock_client_context, "/sites/MySite/Shared Documents")
    # Asserts
    mock_client_context.web.get_folder_by_server_relative_url.assert_called_once_with("/sites/MySite/Shared Documents")
    mock_client_context.load.assert_called_with(mock_folder)
    mock_client_context.execute_query.assert_called()
    assert folder == mock_folder

#
# ----------------- 3. TEST explorer.py (partial) -----------------
#
@pytest.fixture
def mock_explorer_ctx(mocker):
    """
    A fixture returning a MagicMock for the explorer context. 
    We'll mock get_client_context to return this fixture.
    """
    ctx = MagicMock()
    ctx.execute_query.return_value = None
    return ctx


@patch("src.utility_functions.sharepoint_utility.explorer.get_client_context")
def test_connect_and_explore_sharepoint_cascading_no_library(mock_get_client_ctx, mock_explorer_ctx):
    """
    If no matching library is found, code returns library_found=False
    """
    from src.utility_functions.sharepoint_utility.explorer import connect_and_explore_sharepoint_cascading
    from src.utility_functions.sharepoint_utility.common import get_documents_library

    # The "get_client_context" function now returns our mock_explorer_ctx
    mock_get_client_ctx.return_value = mock_explorer_ctx

    # Also mock get_documents_library to return None
    with patch("src.utility_functions.sharepoint_utility.explorer.get_documents_library", return_value=None):
        result = connect_and_explore_sharepoint_cascading(
            base_url="https://my.sharepoint.com",
            site_path="/sites/MySite",
            username="user",
            password="pass",
            library_title="NonExistentLib",
            root_subfolder="General"
        )
        assert result["library_found"] is False
        assert result["file_found"] is False
        assert result["subfolder_found"] is False


@patch("src.utility_functions.sharepoint_utility.explorer.get_client_context")
def test_connect_and_explore_sharepoint_cascading_found(mock_get_client_ctx, mock_explorer_ctx):
    """
    Test the case where library is found, root_subfolder is found,
    but no search_filename is provided => we do a full recursion build_file_tree_df.
    """
    from src.utility_functions.sharepoint_utility.explorer import connect_and_explore_sharepoint_cascading
    # Patch out get_documents_library to return a mock library
    mock_library = MagicMock()
    mock_library.get_property.return_value = MagicMock()  # for RootFolder
    # We'll patch build_file_tree_df to return a dummy DataFrame
    dummy_df = pd.DataFrame([{"Directory": "General", "FileName": "test.txt", "FileUrl": "/sites/..." }])

    mock_get_client_ctx.return_value = mock_explorer_ctx

    with patch("src.utility_functions.sharepoint_utility.explorer.get_documents_library", return_value=mock_library), \
         patch("src.utility_functions.sharepoint_utility.explorer.get_folder_by_server_relative_url") as mock_get_folder, \
         patch("src.utility_functions.sharepoint_utility.explorer.build_file_tree_df", return_value=dummy_df):
        
        mock_target_folder = MagicMock()
        mock_get_folder.return_value = mock_target_folder
        
        result = connect_and_explore_sharepoint_cascading(
            base_url="https://my.sharepoint.com",
            site_path="/sites/MySite",
            username="user",
            password="pass",
            library_title="Documents",
            root_subfolder="General",
            search_filename=None,
            force_full_recursive=False
        )

        assert result["library_found"] is True
        assert result["subfolder_found"] is True
        assert result["file_found"] is False  # because we didn't search for any file
        assert isinstance(result["full_df"], pd.DataFrame)
        # Check that build_file_tree_df was indeed called
        mock_get_folder.assert_called_once()
        # The final DataFrame is our dummy_df
        assert result["full_df"].equals(dummy_df)

#
# ----------------- 4. TEST uploader.py (upload_file_to_sharepoint) -----------------
#
@pytest.fixture
def mock_uploader_ctx(mocker):
    """
    Another fixture for upload context. 
    You might unify these with 'mock_explorer_ctx' if you want a single fixture.
    """
    ctx = MagicMock()
    ctx.execute_query.return_value = None
    return ctx


@patch("src.utility_functions.sharepoint_utility.uploader.get_client_context")
def test_upload_file_to_sharepoint_no_library(mock_get_client_ctx, mock_uploader_ctx):
    """
    If the desired library isn't found, function returns an error dict.
    """
    from src.utility_functions.sharepoint_utility.uploader import upload_file_to_sharepoint
    mock_get_client_ctx.return_value = mock_uploader_ctx

    with patch("src.utility_functions.sharepoint_utility.uploader.get_documents_library", return_value=None):
        result = upload_file_to_sharepoint(
            base_url="https://my.sharepoint.com",
            site_path="/sites/MySite",
            username="user",
            password="pass",
            library_title="NonExistentLib",
            root_subfolder="General",
            local_file_path=None
        )
        assert result["uploaded"] is False
        assert "Could not find document library" in result["error"]


@patch("src.utility_functions.sharepoint_utility.uploader.get_client_context")
def test_upload_file_to_sharepoint_local_file(mock_get_client_ctx, mock_uploader_ctx, tmp_path):
    """
    Test uploading a local file by path.
    """
    from src.utility_functions.sharepoint_utility.uploader import upload_file_to_sharepoint
    mock_get_client_ctx.return_value = mock_uploader_ctx

    # Mock library
    mock_library = MagicMock()
    mock_library.get_property.return_value = MagicMock()  # root folder
    with patch("src.utility_functions.sharepoint_utility.uploader.get_documents_library", return_value=mock_library), \
         patch("src.utility_functions.sharepoint_utility.uploader.get_folder_by_server_relative_url") as mock_get_folder:
        
        mock_folder = MagicMock()
        mock_get_folder.return_value = mock_folder

        # Create a temp file
        test_file = tmp_path / "test_upload.txt"
        test_file.write_text("Hello SharePoint")

        result = upload_file_to_sharepoint(
            base_url="https://my.sharepoint.com",
            site_path="/sites/MySite",
            username="user",
            password="pass",
            library_title="Documents",
            root_subfolder="General",
            local_file_path=str(test_file)
        )

        assert result["uploaded"] is True
        assert result["error"] is None
        # Check that the correct method was called
        mock_folder.upload_file.assert_called_once()
        args, kwargs = mock_folder.upload_file.call_args
        # The second arg should contain the file's bytes
        file_bytes_passed = args[1]
        assert b"Hello SharePoint" in file_bytes_passed

        # The "serverRelativeUrl" might be set by your code upon success
        # so we can also check the final return dict
        # e.g., result["server_relative_url"] == 'some url from your mock'


@patch("src.utility_functions.sharepoint_utility.uploader.get_client_context")
def test_upload_file_to_sharepoint_dataframe(mock_get_client_ctx, mock_uploader_ctx):
    """
    Upload a single DataFrame, expecting it to be converted to CSV bytes.
    """
    from src.utility_functions.sharepoint_utility.uploader import upload_file_to_sharepoint

    mock_get_client_ctx.return_value = mock_uploader_ctx
    mock_library = MagicMock()
    mock_library.get_property.return_value = MagicMock()

    with patch("src.utility_functions.sharepoint_utility.uploader.get_documents_library", return_value=mock_library), \
         patch("src.utility_functions.sharepoint_utility.uploader.get_folder_by_server_relative_url") as mock_get_folder:
        
        mock_folder = MagicMock()
        mock_get_folder.return_value = mock_folder

        df = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})

        result = upload_file_to_sharepoint(
            base_url="https://my.sharepoint.com",
            site_path="/sites/MySite",
            username="user",
            password="pass",
            library_title="Documents",
            root_subfolder="General",
            df=df  # single DataFrame
        )
        assert result["uploaded"] is True
        # The mock folder’s upload_file should be called
        mock_folder.upload_file.assert_called_once()
        args, kwargs = mock_folder.upload_file.call_args
        assert args[0] == "dataframe_upload.csv"  # default name if none specified
        file_bytes = args[1]
        assert b"col1,col2\n1,A\n2,B\n" in file_bytes


