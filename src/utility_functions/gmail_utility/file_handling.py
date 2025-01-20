import os
import re
import zipfile
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
