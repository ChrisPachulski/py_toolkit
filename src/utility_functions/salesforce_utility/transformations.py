import re
from dateutil import parser
import pytz

def flatten_record(record: dict, parent_key: str = "", sep: str = "__") -> dict:
    """
    Recursively flattens a Salesforce record dictionary.
    For relationship fields (sub-dict with 'attributes'), it flattens them.
    """
    items = []
    for key, value in record.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if key == "attributes" and isinstance(value, dict):
            # Skip 'attributes'
            continue
        elif isinstance(value, dict) and "attributes" in value:
            # Relationship
            sub_dict = flatten_record(value, parent_key=new_key, sep=sep)
            items.extend(sub_dict.items())
        else:
            items.append((new_key, value))

    return dict(items)


def convert_to_eastern_time(value) -> str:
    """
    Converts a string that looks like ISO8601 date/time from UTC to US/Eastern.
    Returns original if parsing fails.
    """
    if isinstance(value, str) and re.search(r"\d{4}-\d{2}-\d{2}T", value):
        try:
            dt_utc = parser.parse(value)
            if not dt_utc.tzinfo:
                dt_utc = dt_utc.replace(tzinfo=pytz.utc)
            dt_est = dt_utc.astimezone(pytz.timezone("US/Eastern"))
            return dt_est.strftime("%Y-%m-%d %H:%M:%S %Z")
        except (ValueError, parser.ParserError):
            return value
    return value


def _convert_salesforce_datetime_to_est_str(raw_value: str) -> str:
    """
    Used internally by the report query function for date/datetime cells.
    """
    try:
        dt_utc = parser.parse(raw_value)
        if not dt_utc.tzinfo:
            dt_utc = dt_utc.replace(tzinfo=pytz.utc)
        dt_est = dt_utc.astimezone(pytz.timezone("US/Eastern"))
        return dt_est.strftime("%Y-%m-%d %H:%M:%S %Z")
    except (ValueError, parser.ParserError):
        return raw_value
    
    