import json
import warnings
import pandas as pd
from typing import List, Tuple

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=".*DataFrame concatenation with empty or all-NA entries.*"
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*HTTPResponse.getheader.*"
)

def build_post_analytics_conversations_details_query_payloads(
    df: pd.DataFrame,
    column_name: str,
    intervals: List[Tuple[str, str]],
    chunk_size: int = 10
) -> List[str]:
    """
    Splits conversation IDs into chunks and creates a JSON string for each chunk + interval.
    """
    # Filter out NaN/None conversation IDs and convert them to str
    all_ids = df[column_name].dropna().astype(str).tolist()

    # Split into chunks of size `chunk_size`
    chunks = [all_ids[i : i + chunk_size] for i in range(0, len(all_ids), chunk_size)]

    payloads_json_list = []

    # For each interval, build payloads for every chunk of IDs
    for start_date, end_date in intervals:
        for chunk in chunks:
            payload_dict = {
                "order": "desc",
                "orderBy": "conversationStart",
                "paging": {
                    "pageSize": 50,
                    "pageNumber": 1
                },
                "interval": f"{start_date}T05:00:00.000Z/{end_date}T05:00:00.000Z",
                "segmentFilters": [
                    {"type": "or", "predicates": [{"dimension": "mediaType", "value": "voice"}]},
                    {
                        "type": "or",
                        "predicates": [
                            {"dimension": "direction", "value": "inbound"},
                            {"dimension": "direction", "value": "outbound"},
                        ]
                    }
                ],
                "conversationFilters": [
                    {
                        "type": "or",
                        "predicates": [
                            {"dimension": "conversationId", "value": conv_id}
                            for conv_id in chunk
                        ]
                    }
                ],
                "evaluationFilters": [],
                "surveyFilters": []
            }

            payload_json = json.dumps(payload_dict)
            payloads_json_list.append(payload_json)

    return payloads_json_list


def fetch_all_pages_for_conversations_details_query_payload(api_client, payload_json):
    """
    Given a Genesys API client and a single JSON payload string,
    iterates through all paginated results (pageNumber 1,2,3,...) until no more data.
    Returns a DataFrame of conversation data.
    """
    frames = []
    page_number = 1
    page_size = 50

    while True:
        payload_dict = json.loads(payload_json)
        payload_dict["paging"]["pageNumber"] = page_number

        # POST request
        response_data = api_client.post_analytics_conversations_details_query(payload_dict).to_dict()

        conversations = response_data.get('conversations', [])
        if not conversations:
            break  # No more data

        df_page = pd.json_normalize(conversations)
        frames.append(df_page)

        if len(conversations) < page_size:
            break
        page_number += 1

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fetch_post_analytics_conversations_details_query_df(api_client, intervals, df, column_name):
    """
    1) Build JSON payloads in 10-ID chunks, across intervals.
    2) For each payload, page through all responses.
    3) Combine into one final DataFrame.
    """
    payloads_json_list = build_post_analytics_conversations_details_query_payloads(
        df, column_name, intervals, chunk_size=10
    )

    all_frames = []
    for payload_json in payloads_json_list:
        df_this_payload = fetch_all_pages_for_conversations_details_query_payload(api_client, payload_json)
        if not df_this_payload.empty:
            all_frames.append(df_this_payload)

    return pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()



