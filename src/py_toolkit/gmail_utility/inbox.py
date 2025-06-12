import os
import re
import base64
import pandas as pd
import zipfile

from datetime import datetime
from .file_handling import (
    detect_header, 
    handle_csv,
    handle_xlsx,
    handle_zip,
    handle_tsv
)
from .auth import build_gmail_service


def gmail_reports_inbox(
    search_query='subject: Super Unique Subject',
    stored_file_path=os.path.join(os.path.expanduser('~'), 'Downloads'),
    multiple_files=False
):
    """
    Searches and retrieves email attachments from a Gmail inbox based 
    on the provided search query.

    Parameters:
        search_query (str): Gmail search query (default: 'subject:').
        stored_file_path (str): Directory path to temporarily store downloaded attachments.
        multiple_files (bool): If True, expects multiple sequential files and deletes prior 
                               attachments after reading.

    Returns:
        pd.DataFrame or None: DataFrame containing the content of the found file(s),
                              or None if no matching file is found.
    """

    # Build the Gmail service client (refers to auth.py)
    service = build_gmail_service()

    # 1. Search for messages
    response = service.users().messages().list(userId='me', q=search_query).execute()
    messages = response.get('messages', [])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(
            userId='me',
            q=search_query,
            pageToken=page_token
        ).execute()
        messages.extend(response.get('messages', []))

    if not messages:
        print("No messages found for query:", search_query)
        return None

    # 2. Pick the first message (newest) to fetch attachments
    message_id = messages[0]['id']
    message = service.users().messages().get(userId='me', id=message_id).execute()

    # Print message subject/time
    headers = message["payload"]["headers"]
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    date_header = next((h["value"] for h in headers if h["name"] in ("Received", "Date")), "No Date")
    date_match = re.search(r"\d{1,2}\s\w{3}\s\d{4}\s\d{2}:\d{2}:\d{2}", date_header)
    print(f"Fetching attachment from message '{subject}' (ID: {message_id}) received at {date_match.group() if date_match else 'Unknown date'}")

    # 3. Extract attachments
    payload_parts = message["payload"].get("parts", [])
    for part_num, part in enumerate(payload_parts, start=1):
        filename = part.get('filename')
        if not filename and 'parts' in part:
            # In case there's a nested part that has the actual filename
            for subpart in part['parts']:
                if subpart['filename']:
                    filename = subpart['filename']
                    part = subpart
                    break

        if not filename:
            continue  # No attachment in this part

        data = None
        body = part.get('body', {})
        # If inline data
        if 'data' in body:
            data = body['data']
        # If there's an attachment ID
        elif 'attachmentId' in body:
            att_id = body['attachmentId']
            att = service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=att_id
            ).execute()
            data = att.get('data')

        if data:
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            path = os.path.join(stored_file_path, filename)
            with open(path, 'wb') as f:
                f.write(file_data)
            print(f"Attachment saved to: {path}")
        else:
            print(f"No data found for filename: {filename}")

    # 4. Find downloaded files in `stored_file_path`
    files_found = [f for f in os.listdir(stored_file_path) if os.path.isfile(os.path.join(stored_file_path, f))]
    if not files_found:
        print("No files downloaded or directory is empty.")
        return None

    # Filter for typical file patterns (CSV, XLSX, ZIP, TSV) — logic in file_handling
    # Or you can inline it here.
    for file in files_found:
        full_path = os.path.join(stored_file_path, file)
        file_lower = file.lower()

        if file_lower.endswith('.csv'):
            df = handle_csv(full_path)
        elif file_lower.endswith('.xlsx') or file_lower.endswith('.xls'):
            df = handle_xlsx(full_path)
        elif file_lower.endswith('.zip'):
            df = handle_zip(full_path, stored_file_path)
        elif file_lower.endswith('.tsv'):
            df = handle_tsv(full_path)
        else:
            print(f"Skipping unknown filetype: {file}")
            continue

        if multiple_files:
            # If we are expecting multiple files, let's remove the file so future runs won’t reuse it
            os.remove(full_path)
            print(f"Removed {full_path}")

        return df

    return None
