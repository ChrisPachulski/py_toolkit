import os
import re
import base64
import zipfile
from io import StringIO
from email import encoders
from email.mime.base import MIMEBase
import pandas as pd

def detect_header(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    previous_line = None
    for index, line in enumerate(lines):
        if "," in line and not any(part.strip().isdigit() for part in line.split(',')):
            if previous_line and line != previous_line:
                return index
        previous_line = line
    return None

def handle_csv(full_path):
    df = pd.read_csv(full_path, on_bad_lines='skip', encoding='utf-8')
    if df.shape[0] <= 1:
        # Possibly no proper header row
        header_index = detect_header(full_path)
        if header_index is not None:
            df = pd.read_csv(full_path, header=header_index).reset_index(drop=True)
            new_header = df.iloc[0]
            df = df[1:].reset_index(drop=True)
            df.columns = new_header
    return df

def handle_xlsx(full_path):
    return pd.read_excel(full_path)

def handle_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_to)
    # If you know it’s specifically extracting a CSV, load it:
    extracted_files = z.namelist()
    csv_files = [f for f in extracted_files if f.lower().endswith('.csv')]
    if csv_files:
        csv_path = os.path.join(extract_to, csv_files[0])
        return handle_csv(csv_path)
    # else handle other extracted files
    return None

def handle_tsv(full_path):
    return pd.read_csv(full_path, sep='\t', on_bad_lines='skip')


def create_attachment(data, file_title):
    """
    Given a single piece of data and a corresponding file title:
      - If `data` is a Pandas DataFrame, convert to CSV and attach.
      - If `data` is a string path to a file on disk, attach the file.
    Returns a MIMEBase part ready to attach to the email.
    """
    if isinstance(data, pd.DataFrame):
        csv_buffer = StringIO()
        data.to_csv(csv_buffer, index=False)
        attachment_data = csv_buffer.getvalue().encode('utf-8')

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={file_title}')
        return part
    
    elif isinstance(data, str) and os.path.isfile(data):
        # If the argument is a string, we assume it's a local file path.
        with open(data, 'rb') as fp:
            attachment_data = fp.read()
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(data)}')
        return part
    
    else:
        raise ValueError(
            "Unsupported `data` type or invalid file path. "
            "Must be a pd.DataFrame or valid file path string."
        )


def create_attachments(data_list, file_titles):
    """
    Given lists of data objects and file_titles, create MIME attachments.
    Ensures both lists have the same length. Returns a list of MIMEBase parts.
    """
    # Convert to list if single items provided.
    if not isinstance(data_list, list):
        data_list = [data_list]
    if not isinstance(file_titles, list):
        file_titles = [file_titles]

    if len(data_list) != len(file_titles):
        raise ValueError(
            "The number of data items must match the number of file titles."
        )

    parts = []
    for d, title in zip(data_list, file_titles):
        part = create_attachment(d, title)
        parts.append(part)
    return parts