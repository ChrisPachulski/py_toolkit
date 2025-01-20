import os
from io import BytesIO
from pathlib import Path
import pandas as pd
import janitor

from office365.sharepoint.files.file import File

# Import from your common and auth modules
from .auth import get_client_context
from .common import get_documents_library, get_folder_by_server_relative_url


def build_file_tree_df(folder, ctx, current_path=""):
    """
    Recursively build a DataFrame of all folders/files under `folder`.
    Columns: ['Directory', 'FileName', 'FileUrl']
    """
    records = []
    folder_name = folder.properties.get("Name", "")
    this_path = os.path.join(current_path, folder_name)

    # Gather files in this folder
    files = folder.files
    ctx.load(files)
    ctx.execute_query()

    for f in files:
        file_name = f.properties.get("Name", "")
        file_url = f.properties.get("ServerRelativeUrl", "")
        records.append({
            "Directory": this_path,
            "FileName": file_name,
            "FileUrl": file_url
        })

    # Recursively process subfolders
    subfolders = folder.folders
    ctx.load(subfolders)
    ctx.execute_query()

    for sf in subfolders:
        sub_df = build_file_tree_df(sf, ctx, this_path)
        records.extend(sub_df.to_dict("records"))

    return pd.DataFrame(records)


def load_tabular_file(ctx, file_url, sheet_name=None):
    """
    Download and load Excel/CSV/TSV as a DataFrame. 
    Returns None if file type is not recognized.
    """
    file_result = File.open_binary(ctx, file_url)
    file_bytes = file_result.content
    _, ext = os.path.splitext(file_url.lower())

    if ext in [".xlsx", ".xls"]:
        return _load_excel_file(file_bytes, sheet_name)
    elif ext in [".csv", ".tsv"]:
        return _load_csv_file(file_bytes, ext)
    else:
        print(f"Not a recognized tabular file type: {file_url}")
        return None


def _load_excel_file(file_bytes, sheet_name=None):
    with BytesIO(file_bytes) as bio:
        xls = pd.ExcelFile(bio)
        if sheet_name is None:
            print("Found sheet names:", xls.sheet_names)
            print("Provide a sheet_name to load a specific worksheet.")
            return None
        else:
            return pd.read_excel(bio, sheet_name=sheet_name).clean_names()


def _load_csv_file(file_bytes, ext):
    sep = "," if ext == ".csv" else "\t"
    with BytesIO(file_bytes) as bio:
        df = pd.read_csv(bio, sep=sep).clean_names()
    return df


def connect_and_explore_sharepoint_cascading(
    base_url=None,
    site_path=None,
    username=None,
    password=None,
    library_title="Documents",
    root_subfolder="General",
    search_filename=None,
    sheet_name=None,
    force_full_recursive=False
):
    """
    A cascading, high-level convenience function:
      1) Connect to SharePoint (env vars or passed in).
      2) Retrieve 'library_title'.
      3) Build a server-relative path for 'root_subfolder'.
      4) If search_filename is given, try a quick search in that folder's immediate files.
         If not found, do deeper search if needed.
      5) If search_filename is None (or force_full_recursive=True), build the entire file tree.
      6) Return a dictionary with context, booleans, file DataFrame, and optional tabular DataFrame.

      Extended:
      - If we find a file but it is not recognized as a tabular file, 
        we'll download it to the user's Downloads folder.
    """

    ctx = get_client_context(base_url, site_path, username, password)

    # 2) Get document library
    documents_lib = get_documents_library(ctx, library_title)
    if not documents_lib:
        print(f"Could not find '{library_title}' library.")
        return {
            "ctx": ctx,
            "library_found": False,
            "subfolder_found": False,
            "file_found": False,
            "full_df": None,
            "df_tabular": None
        }

    # Load the library's root folder
    ctx.load(documents_lib, ["RootFolder"])
    ctx.execute_query()
    root_folder_obj = documents_lib.get_property("RootFolder")

    ctx.load(root_folder_obj, ["ServerRelativeUrl"])
    ctx.execute_query()
    library_root_url = root_folder_obj.get_property("ServerRelativeUrl")

    # 3) Build server-relative path
    if root_subfolder:
        normalized_subfolder = root_subfolder.strip("/")
        full_path = library_root_url.rstrip("/") + "/" + normalized_subfolder
        try:
            target_folder = get_folder_by_server_relative_url(ctx, full_path)
        except Exception as e:
            print(f"Could not locate folder path '{full_path}' in '{library_title}'. Error:")
            print(e)
            return {
                "ctx": ctx,
                "library_found": True,
                "subfolder_found": False,
                "file_found": False,
                "full_df": None,
                "df_tabular": None
            }
    else:
        print(f"No root_subfolder specified; using the library root: '{library_title}'")
        target_folder = get_folder_by_server_relative_url(ctx, library_root_url)

    file_found = False
    df_tabular = None
    full_df = None

    def load_or_download_file(context, file_url, file_name, sheet=None):
        """
        Attempt to load a file as tabular (csv/xls/xlsx).
        If not recognized, download it to the local Downloads folder instead.
        """
        tabular_exts = {'.xls', '.xlsx', '.csv'}
        _, ext = os.path.splitext(file_name.lower())

        if ext in tabular_exts:
            df_local = load_tabular_file(context, file_url, sheet)
            return df_local, False
        else:
            downloads_folder = Path.home() / "Downloads"
            downloads_folder.mkdir(parents=True, exist_ok=True)
            local_path = downloads_folder / file_name

            print(f"Downloading '{file_name}' to '{local_path}' ...")
            with open(local_path, 'wb') as local_file:
                file = context.web.get_file_by_server_relative_url(file_url)
                file.download(local_file)
                context.execute_query()

            return None, True

    # 4) Possibly search for a file quickly
    if search_filename and not force_full_recursive:
        target_folder_files = target_folder.files
        ctx.load(target_folder_files)
        ctx.execute_query()

        matched_file_url = None
        matched_file_name = None
        for f in target_folder_files:
            sp_file_name = f.properties.get("Name", "")
            if search_filename.lower() in sp_file_name.lower():
                matched_file_url = f.properties.get("ServerRelativeUrl")
                matched_file_name = sp_file_name
                break

        if matched_file_url:
            file_found = True
            df_tabular_local, was_downloaded = load_or_download_file(ctx, matched_file_url, matched_file_name, sheet_name)
            df_tabular = df_tabular_local
            return {
                "ctx": ctx,
                "library_found": True,
                "subfolder_found": True,
                "file_found": file_found,
                "was_downloaded": was_downloaded,
                "full_df": None,
                "df_tabular": df_tabular
            }
        else:
            print(f"'{search_filename}' not found at immediate level of '{root_subfolder or library_title}'.")
            print("Attempting deeper search...")
            full_df = build_file_tree_df(target_folder, ctx)
            df_match = full_df[full_df["FileName"].str.lower().str.contains(search_filename.lower())]
            if not df_match.empty:
                file_found = True
                matched_file_url = df_match.iloc[0]["FileUrl"]
                matched_file_name = df_match.iloc[0]["FileName"]
                df_tabular_local, was_downloaded = load_or_download_file(ctx, matched_file_url, matched_file_name, sheet_name)
                df_tabular = df_tabular_local
            else:
                print(f"Could not find '{search_filename}' in deeper subfolders of '{root_subfolder or library_title}'.")

            return {
                "ctx": ctx,
                "library_found": True,
                "subfolder_found": True,
                "file_found": file_found,
                "was_downloaded": (file_found and df_tabular is None),
                "full_df": full_df,
                "df_tabular": df_tabular
            }

    # 5) If no search_filename or forced recursion, build full tree
    print(f"Building file tree under '{root_subfolder or library_title}'...")
    full_df = build_file_tree_df(target_folder, ctx)

    # 6) If user provided a search_filename but also wants full recursion
    if search_filename:
        df_match = full_df[full_df["FileName"].str.lower().str.contains(search_filename.lower())]
        if not df_match.empty:
            file_found = True
            matched_file_url = df_match.iloc[0]["FileUrl"]
            matched_file_name = df_match.iloc[0]["FileName"]
            df_tabular_local, was_downloaded = load_or_download_file(ctx, matched_file_url, matched_file_name, sheet_name)
            df_tabular = df_tabular_local
        else:
            print(f"'{search_filename}' not found in '{root_subfolder or library_title}' after full recursion.")

    return {
        "ctx": ctx,
        "library_found": True,
        "subfolder_found": bool(root_subfolder),
        "file_found": file_found,
        "was_downloaded": (file_found and df_tabular is None),
        "full_df": full_df,
        "df_tabular": df_tabular
    }


# =================== Convenience Wrapper(s) (Explorer) ===================

def sharepoint_known_explorer(
    library_title="Documents",
    root_subfolder="General",
    search_filename=None,
    sheet_name=None,
    force_full_recursive=False
):
    """
    Connect to a known SharePoint site using environment variables, 
    then explore the specified document library and subfolder.
    """
    base_url = os.getenv('SP_BASE')
    site_path = os.getenv('SP_DIR')
    username = os.getenv('MAIN_USER')
    password = os.getenv('MAIN_PWD')
    return connect_and_explore_sharepoint_cascading(
        base_url, 
        site_path, 
        username, 
        password, 
        library_title,
        root_subfolder,
        search_filename,
        sheet_name,
        force_full_recursive
    )

