import re

def clean_genesys_id_column(df, column_name):
    """
    Strips any prefix up to '/', removes invalid placeholders,
    and enforces a valid UUID pattern for Genesys.
    """
    df[column_name] = df[column_name].str.replace(r'^.*/', '', regex=True)

    # Remove rows with 'Pending' or 'admin'
    df = df[df[column_name] != 'Pending']
    df = df[df[column_name] != 'admin']

    # Only keep rows that match a UUID pattern
    df = df[df[column_name].str.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', na=False)]

    return df

