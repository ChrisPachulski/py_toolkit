import os
import requests
import pandas as pd
import janitor
from dotenv import load_dotenv
from .common import _get_env_path
from .transformations import _convert_salesforce_datetime_to_est_str

def query_salesforce_report(report_id: str) -> pd.DataFrame:
    """
    Queries a Salesforce report (via Analytics API) by its ID and returns the data as a DataFrame.
    """
    load_dotenv(dotenv_path=_get_env_path())
    refresh_token = os.getenv("SF_REFRESH")
    if not refresh_token:
        raise ValueError("SF_REFRESH token is missing from the .env file.")

    base_url = "https://acftac.my.salesforce.com"
    api_version = "v60.0"
    endpoint = f"{base_url}/services/data/{api_version}/analytics/reports/{report_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {refresh_token}",
    }

    response = requests.get(endpoint, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.reason}")
        print("Response Text:", response.text)
        return pd.DataFrame()  # or None

    report_json = response.json()
    if not report_json:
        return pd.DataFrame()

    detail_cols = report_json.get("reportMetadata", {}).get("detailColumns", [])
    detail_info = report_json.get("reportExtendedMetadata", {}).get("detailColumnInfo", {})

    # Map each detail column to its dataType
    column_data_types = {}
    for col_api_name in detail_cols:
        meta = detail_info.get(col_api_name, {})
        column_data_types[col_api_name] = meta.get("dataType", None)

    fact_map = report_json.get("factMap", {})
    all_rows = []

    # Each factMap key corresponds to a grouping or "bucket" of rows
    for fm_key, fm_value in fact_map.items():
        rows = fm_value.get("rows", [])
        for row in rows:
            data_cells = row.get("dataCells", [])
            row_dict = {}

            for i, cell in enumerate(data_cells):
                col_api_name = detail_cols[i]
                col_type = column_data_types.get(col_api_name)
                raw_value = cell.get("value")
                label_value = cell.get("label")

                if col_type in ("date", "datetime"):
                    # Convert UTC date/time to EST if possible
                    if raw_value:
                        row_dict[col_api_name] = _convert_salesforce_datetime_to_est_str(raw_value)
                    else:
                        row_dict[col_api_name] = None
                else:
                    # For non-date fields, prefer the label if it's not "-"
                    display_value = label_value if label_value and label_value != "-" else raw_value
                    row_dict[col_api_name] = display_value

            all_rows.append(row_dict)

    return pd.DataFrame(all_rows).clean_names()

