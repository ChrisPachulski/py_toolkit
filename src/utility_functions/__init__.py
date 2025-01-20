# ================== SHAREPOINT ==================
from .sharepoint_utility import (
    # From auth.py
    get_client_context,

    # From explorer.py
    connect_and_explore_sharepoint_cascading,
    sharepoint_tpg_call_center_explorer,
    sharepoint_tpg_training_explorer,
    sharepoint_tpg_orr_ncc_explorer,
    build_file_tree_df,
    load_tabular_file,

    # From uploader.py
    upload_file_to_sharepoint,
    sharepoint_tpg_call_center_upload,
    sharepoint_tpg_training_upload,
    sharepoint_tpg_orr_ncc_upload
)

# ================== SALESFORCE ==================
from .salesforce_utility import (
    # From auth.py
    get_salesforce_refresh_token,
    print_salesforce_authorize_url,

    # From query.py
    query_salesforce_soql,

    # From reporting.py
    query_salesforce_report,

    # Potentially transformations if you want them top-level
    flatten_record,
    convert_to_eastern_time
)

# ================== GENESYS ==================
from .genesys_utility import (
    # From auth.py
    get_genesys_access_token,

    # From users.py
    genesys_users_setup,

    # From conversation.py
    genesys_conversation_setup,

    # From conversation_details_query.py
    build_post_analytics_conversations_details_query_payloads,
    fetch_all_pages_for_conversations_details_query_payload,
    fetch_post_analytics_conversations_details_query_df,

    # From transformations.py
    clean_genesys_id_column
)

# If you want to define a single __all__ that collects everything:
__all__ = [
    # SHAREPOINT
    "get_client_context",
    "connect_and_explore_sharepoint_cascading",
    "sharepoint_tpg_call_center_explorer",
    "sharepoint_tpg_training_explorer",
    "sharepoint_tpg_orr_ncc_explorer",
    "build_file_tree_df",
    "load_tabular_file",
    "upload_file_to_sharepoint",
    "sharepoint_tpg_call_center_upload",
    "sharepoint_tpg_training_upload",
    "sharepoint_tpg_orr_ncc_upload",

    # SALESFORCE
    "get_salesforce_refresh_token",
    "print_salesforce_authorize_url",
    "query_salesforce_soql",
    "query_salesforce_report",
    "flatten_record",
    "convert_to_eastern_time",

    # GENESYS
    "get_genesys_access_token",
    "genesys_users_setup",
    "genesys_conversation_setup",
    "build_post_analytics_conversations_details_query_payloads",
    "fetch_all_pages_for_conversations_details_query_payload",
    "fetch_post_analytics_conversations_details_query_df",
    "clean_genesys_id_column",
]
