from .auth import get_client_context
from .common import (
    get_documents_library,
    get_folder_by_server_relative_url,
    get_subfolder_by_name
)
from .explorer import (
    build_file_tree_df,
    load_tabular_file,
    connect_and_explore_sharepoint_cascading,
    # convenience wrappers
    sharepoint_known_explorer
)
from .uploader import (
    upload_file_to_sharepoint,
    # convenience wrappers
    sharepoint_known_upload,
)

# Optionally define __all__ to limit what is imported via "from sharepoint_utility import *"
__all__ = [
    "get_client_context",
    "get_documents_library",
    "get_folder_by_server_relative_url",
    "get_subfolder_by_name",
    "build_file_tree_df",
    "load_tabular_file",
    "connect_and_explore_sharepoint_cascading",
    "upload_file_to_sharepoint",
    "sharepoint_known_explorer",
    "sharepoint_known_upload",
]