import os
import requests
import pandas as pd
import janitor
from dotenv import load_dotenv
from .common import _get_env_path
from .transformations import flatten_record, convert_to_eastern_time

def query_salesforce_soql(query_string: str) -> pd.DataFrame:
    """
    Executes a SOQL query against Salesforce, returns the results in a flattened DataFrame.
    """
    load_dotenv(dotenv_path=_get_env_path())
    refresh_token = os.getenv("SF_REFRESH")
    if not refresh_token:
        raise ValueError("Missing 'SF_REFRESH' token in .env file.")

    base_url = "https://acftac.my.salesforce.com"
    api_version = "v60.0"
    endpoint = f"{base_url}/services/data/{api_version}/query/?q="

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {refresh_token}",
    }

    response = requests.get(endpoint + query_string, headers=headers)
    response.raise_for_status()

    data = response.json()
    records = data.get("records", [])

    flattened_rows = []
    for record in records:
        flat_record = flatten_record(record)
        # Convert potential date/time strings to EST
        for k, v in flat_record.items():
            flat_record[k] = convert_to_eastern_time(v)
        flattened_rows.append(flat_record)

    return pd.DataFrame(flattened_rows).clean_names()

