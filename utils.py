import re
from datetime import datetime

def split_string(input_string: str) -> list:
    return input_string.split(',')

def format_date(input_date: str) -> str:
    try:
        date_obj = datetime.strptime(input_date, '%Y-%m-%d')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return "Invalid date format"

def count_numeric_in_guid(guid: str) -> int:
    numeric_count = sum(c.isdigit() for c in guid)
    return numeric_count
