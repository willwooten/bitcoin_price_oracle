"""General helpers."""
from datetime import datetime, timezone


def get_day_of_month(timestamp: int) -> int:
    """
    Get the day of the month from a given timestamp.

    :param timestamp: The timestamp.
    :type timestamp: int
    :return: The day of the month.
    :rtype: int
    """
    return int(datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%d"))


def is_valid_date(date_string: str) -> bool:
    """
    Check if a date string is in valid format.

    This function checks if a given date string is in the format "YYYY-MM-DD".

    :param date_string: The date string to be validated.
    :type date_string: str
    :return: True if the date string is in valid format, False otherwise.
    :rtype: bool
    """
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_date(date: datetime) -> datetime:
    """
    Format a date string into a datetime object.

    This function takes a date string in the format "YYYY-MM-DD" and converts it
    into a datetime object.

    :param date: The date string to be formatted.
    :type date: str
    :return: The formatted datetime object.
    :rtype: datetime
    """
    return datetime.strptime(date, "%Y-%m-%d")
