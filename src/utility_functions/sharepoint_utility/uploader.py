import os
from io import BytesIO, StringIO
import pandas as pd
import openpyxl

from .auth import get_client_context
from .common import get_documents_library, get_folder_by_server_relative_url

def upload_file_to_sharepoint(
    base_url=None,
    site_path=None,
    username=None,
    password=None,
    library_title="Documents",
    root_subfolder="General",
    local_file_path=None,
    file_bytes=None,
    sharepoint_file_name=None,
    df=None,
    dfs_dict_list=None
):
    """
    Upload a file (local path, in-memory bytes, or DataFrame(s)) to SharePoint 
    under the specified library and subfolder path.
    Supports:
      1) local_file_path,
      2) raw bytes (file_bytes),
      3) single DataFrame (CSV),
      4) multiple DataFrames (XLSX with multiple sheets).
    """

    # 1) Build context
    try:
        ctx = get_client_context(base_url, site_path, username, password)
    except Exception as exc:
        return {
            "uploaded": False,
            "server_relative_url": None,
            "error": f"Failed to get ClientContext: {exc}"
        }

    # 2) Locate desired library
    documents_lib = get_documents_library(ctx, library_title)
    if not documents_lib:
        return {
            "uploaded": False,
            "server_relative_url": None,
            "error": f"Could not find document library '{library_title}'."
        }

    # 3) Retrieve library root folder's ServerRelativeUrl
    ctx.load(documents_lib, ["RootFolder"])
    ctx.execute_query()
    root_folder_obj = documents_lib.get_property("RootFolder")

    ctx.load(root_folder_obj, ["ServerRelativeUrl"])
    ctx.execute_query()
    library_root_url = root_folder_obj.get_property("ServerRelativeUrl")

    # 4) Build target folder path
    if root_subfolder:
        normalized_subfolder = root_subfolder.strip("/")
        folder_url = library_root_url.rstrip("/") + "/" + normalized_subfolder
    else:
        folder_url = library_root_url

    # 5) Attempt to get folder reference
    try:
        target_folder = get_folder_by_server_relative_url(ctx, folder_url)
    except Exception as exc:
        return {
            "uploaded": False,
            "server_relative_url": None,
            "error": f"Could not locate folder path '{folder_url}'. Error: {exc}"
        }

    # 6) Determine data to upload
    final_bytes = None

    # Multiple DataFrames => single XLSX
    if dfs_dict_list is not None:
        if sharepoint_file_name is None:
            sharepoint_file_name = "multiple_dfs.xlsx"
        bytes_buffer = BytesIO()
        with pd.ExcelWriter(bytes_buffer, engine='openpyxl') as writer:
            for entry in dfs_dict_list:
                tab_name = entry["tab_name"]
                dataframe = entry["dataframe"]
                dataframe.to_excel(writer, sheet_name=tab_name, index=False)
        final_bytes = bytes_buffer.getvalue()

    # Single DataFrame => CSV
    elif df is not None:
        if sharepoint_file_name is None:
            sharepoint_file_name = "dataframe_upload.csv"
        str_buffer = StringIO()
        df.to_csv(str_buffer, index=False)
        final_bytes = str_buffer.getvalue().encode("utf-8")

    # local_file_path => read from disk
    elif local_file_path:
        if sharepoint_file_name is None:
            sharepoint_file_name = os.path.basename(local_file_path)
        try:
            with open(local_file_path, "rb") as f:
                final_bytes = f.read()
        except Exception as exc:
            return {
                "uploaded": False,
                "server_relative_url": None,
                "error": f"Could not read local file '{local_file_path}': {exc}"
            }

    # Raw bytes
    elif file_bytes is not None:
        if sharepoint_file_name is None:
            return {
                "uploaded": False,
                "server_relative_url": None,
                "error": "Must provide sharepoint_file_name if only passing file_bytes."
            }
        final_bytes = file_bytes

    else:
        return {
            "uploaded": False,
            "server_relative_url": None,
            "error": "No data provided (df, dfs_dict_list, local_file_path, or file_bytes)."
        }

    # 7) Perform the upload
    try:
        uploaded_file = target_folder.upload_file(sharepoint_file_name, final_bytes).execute_query()
        return {
            "uploaded": True,
            "server_relative_url": uploaded_file.serverRelativeUrl,
            "error": None
        }
    except Exception as exc:
        return {
            "uploaded": False,
            "server_relative_url": None,
            "error": f"Failed to upload file '{sharepoint_file_name}': {exc}"
        }


# =================== Convenience Wrappers (Uploader) ===================

def sharepoint_known_upload(
    library_title="Documents",
    root_subfolder="General",
    local_file_path=None,
    file_bytes=None,
    sharepoint_file_name=None,
    df=None,
    dfs_dict_list=None
):
    """
    Upload data to a known SharePoint site using environment variables.
    """
    base_url = os.getenv('SP_BASE')
    site_path = os.getenv('SP_DIR')
    username = os.getenv('MAIN_USER')
    password = os.getenv('MAIN_PWD')
    return upload_file_to_sharepoint(
        base_url=base_url,
        site_path=site_path,
        username=username,
        password=password,
        library_title=library_title,
        root_subfolder=root_subfolder,
        local_file_path=local_file_path,
        file_bytes=file_bytes,
        sharepoint_file_name=sharepoint_file_name,
        df=df,
        dfs_dict_list=dfs_dict_list
    )

