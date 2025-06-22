"""PowerBuilder built-in functions for expression evaluation.

This module provides implementations of common PowerBuilder built-in functions
that can be used with the expression evaluator.
"""

import datetime
import math
from typing import Any, Callable


def create_builtin_functions() -> dict[str, Callable]:



    
    


    """Create a dictionary of PowerBuilder built-in functions.
    
    Returns:
        Dictionary mapping function names to their implementations
    """
    return {
        # String functions
        "len": pb_len, "lenw": pb_len, # Wide char version, same as len in Python
        "trim": pb_trim, "ltrim": pb_ltrim, "rtrim": pb_rtrim, "upper": pb_upper, "lower": pb_lower, "mid": pb_mid, "pos": pb_pos, "replace": pb_replace, "left": pb_left, "right": pb_right, "reverse": pb_reverse, "space": pb_space, "fill": pb_fill, # Numeric functions
        "abs": abs, "ceiling": math.ceil, "floor": math.floor, "int": pb_int, "long": pb_long, "round": pb_round, "truncate": pb_truncate, "mod": pb_mod, "sign": pb_sign, "sqrt": math.sqrt, "exp": math.exp, "log": math.log, "sin": math.sin, "cos": math.cos, "tan": math.tan, "pi": lambda: math.pi, "rand": pb_rand, "randomize": pb_randomize, # Date/Time functions
        "today": pb_today, "now": pb_now, "year": pb_year, "month": pb_month, "day": pb_day, "hour": pb_hour, "minute": pb_minute, "second": pb_second, "dayname": pb_dayname, "daynumber": pb_daynumber, "daysafter": pb_daysafter, "secondsafter": pb_secondsafter, "relativedate": pb_relativedate, "relativetime": pb_relativetime, # Type checking/conversion
        "isnull": pb_isnull, "isvalid": pb_isvalid, "isnumber": pb_isnumber, "isdate": pb_isdate, "istime": pb_istime, "string": pb_string, "real": pb_real, "double": pb_double, "integer": pb_integer, "boolean": pb_boolean, "date": pb_date, "time": pb_time, "datetime": pb_datetime, "dec": pb_decimal, "decimal": pb_decimal, # Array functions
        "upperbound": pb_upperbound, "lowerbound": pb_lowerbound, # Miscellaneous
        "if": pb_if, "choose": pb_choose, "case": pb_case, "max": max, "min": min, }


# String Functions
def pb_len(s: str) -> int:

    
    
    """Return length of string."""
    return len(s) if s is not None else 0


def pb_trim(s: str) -> str:



    
    


    """Remove leading and trailing spaces."""
    return s.strip() if s is not None else ""


def pb_ltrim(s: str) -> str:



    
    


    """Remove leading spaces."""
    return s.lstrip() if s is not None else ""


def pb_rtrim(s: str) -> str:



    
    


    """Remove trailing spaces."""
    return s.rstrip() if s is not None else ""


def pb_upper(s: str) -> str:



    
    


    """Convert to uppercase."""
    return s.upper() if s is not None else ""


def pb_lower(s: str) -> str:



    
    


    """Convert to lowercase."""
    return s.lower() if s is not None else ""


def pb_mid(s: str, start: int, length: int = None) -> str:



    
    


    """Extract substring. PowerBuilder uses 1-based indexing."""
    if s is None:
        return ""
    start = max(1, start)  # Ensure positive
    start_idx = start - 1  # Convert to 0-based
    
    if length is None:
        return s[start_idx:]
    else:
        return s[start_idx:start_idx + length]


def pb_pos(haystack: str, needle: str, start: int = 1) -> int:



    
    


    """Find position of substring. Returns 0 if not found."""
    if haystack is None or needle is None:
        return 0
    
    start_idx = max(0, start - 1)  # Convert to 0-based
    pos = haystack.find(needle, start_idx)
    return pos + 1 if pos >= 0 else 0  # Convert back to 1-based


def pb_replace(s: str, old: str, new: str, start: int = 1, count: int = 0) -> str:



    
    


    """Replace occurrences of substring."""
    if s is None:
        return ""
    
    if count == 0:
        # Replace all occurrences from start position
        before = s[:start-1] if start > 1 else ""
        after = s[start-1:].replace(old, new)
        return before + after
    else:
        # Replace limited number of occurrences
        before = s[:start-1] if start > 1 else ""
        after = s[start-1:].replace(old, new, count)
        return before + after


def pb_left(s: str, n: int) -> str:



    
    


    """Return leftmost n characters."""
    if s is None:
        return ""
    return s[:n]


def pb_right(s: str, n: int) -> str:



    
    


    """Return rightmost n characters."""
    if s is None:
        return ""
    return s[-n:] if n > 0 else ""


def pb_reverse(s: str) -> str:



    
    


    """Reverse a string."""
    if s is None:
        return ""
    return s[::-1]


def pb_space(n: int) -> str:



    
    


    """Return string of n spaces."""
    return " " * max(0, n)


def pb_fill(s: str, n: int) -> str:



    
    


    """Return string repeated n times."""
    if s is None:
        return ""
    return s * max(0, n)


# Numeric Functions
def pb_int(value: Any) -> int:

    
    
    """Convert to integer."""
    if value is None:
        return 0
    if isinstance(value, str):
        # Remove whitespace and handle empty string
        value = value.strip()
        if not value:
            return 0
        # Handle decimal strings
        try:
            return int(float(value))
        except ValueError:
            return 0
    return int(value)


def pb_long(value: Any) -> int:



    
    


    """Convert to long (same as int in Python)."""
    return pb_int(value)


def pb_round(value: int | float, decimals: int= 0) -> int | float:



    
    


    """Round to specified decimal places."""
    if value is None:
        return 0
    result = round(value, decimals)
    return int(result) if decimals == 0 else result


def pb_truncate(value: int | float, decimals: int= 0) -> int | float:



    
    


    """Truncate to specified decimal places."""
    if value is None:
        return 0
    if decimals == 0:
        return int(value)
    factor = 10 ** decimals
    return int(value * factor) / factor


def pb_mod(a: int | float, b: int | float) -> int | float:



    
    


    """Modulo operation."""
    if b == 0:
        raise ValueError("Division by zero in mod operation")
    return a % b


def pb_sign(value: int | float) -> int:



    
    


    """Return sign of number: -1, 0, or 1."""
    if value is None:
        return 0
    if value > 0:
        return 1
    elif value < 0:
        return -1
    else:
        return 0


def pb_rand(n: int) -> int:



    
    


    """Return random integer between 1 and n."""
    import random
    return random.randint(1, max(1, n))


def pb_randomize(seed: int = None) -> None:



    
    


    """Set random seed."""
    import random
    if seed is not None:
        random.seed(seed)


# Date/Time Functions
def pb_today() -> datetime.date:

    
    
    """Return today's date."""
    return datetime.date.today()


def pb_now() -> datetime.datetime:



    
    


    """Return current date and time."""
    return datetime.datetime.now()


def pb_year(date: datetime.date | datetime.datetime) -> int:



    
    


    """Extract year from date."""
    if date is None:
        return 0
    return date.year


def pb_month(date: datetime.date | datetime.datetime) -> int:



    
    


    """Extract month from date."""
    if date is None:
        return 0
    return date.month


def pb_day(date: datetime.date | datetime.datetime) -> int:



    
    


    """Extract day from date."""
    if date is None:
        return 0
    return date.day


def pb_hour(time: datetime.time | datetime.datetime) -> int:



    
    


    """Extract hour from time."""
    if time is None:
        return 0
    return time.hour


def pb_minute(time: datetime.time | datetime.datetime) -> int:



    
    


    """Extract minute from time."""
    if time is None:
        return 0
    return time.minute


def pb_second(time: datetime.time | datetime.datetime) -> int:



    
    


    """Extract second from time."""
    if time is None:
        return 0
    return time.second


def pb_dayname(date: datetime.date | datetime.datetime) -> str:



    
    


    """Return day name (e.g., 'Monday')."""
    if date is None:
        return ""
    return date.strftime("%A")


def pb_daynumber(date: datetime.date | datetime.datetime) -> int:



    
    


    """Return day of week (1=Sunday, 7=Saturday)."""
    if date is None:
        return 0
    # Python: Monday=0, Sunday=6
    # PowerBuilder: Sunday=1, Saturday=7
    return (date.weekday() + 1) % 7 + 1


def pb_daysafter(date1: datetime.date | datetime.datetime, date2: datetime.date | datetime.datetime) -> int:



    
    


    """Return days between dates."""
    if date1 is None or date2 is None:
        return 0
    # Convert datetime to date if needed
    if isinstance(date1, datetime.datetime):
        date1 = date1.date()
    if isinstance(date2, datetime.datetime):
        date2 = date2.date()
    return (date2 - date1).days


def pb_secondsafter(time1: datetime.time | datetime.datetime, time2: datetime.time | datetime.datetime) -> int:



    
    


    """Return seconds between times."""
    if time1 is None or time2 is None:
        return 0
    # Convert to datetime if needed
    if isinstance(time1, datetime.time):
        time1 = datetime.datetime.combine(datetime.date.today(), time1)
    if isinstance(time2, datetime.time):
        time2 = datetime.datetime.combine(datetime.date.today(), time2)
    return int((time2 - time1).total_seconds())


def pb_relativedate(date: datetime.date | datetime.datetime, days: int) -> datetime.date:



    
    


    """Add days to date."""
    if date is None:
        return datetime.date.today()
    if isinstance(date, datetime.datetime):
        date = date.date()
    return date + datetime.timedelta(days=days)


def pb_relativetime(time: datetime.time | datetime.datetime, seconds: int) -> datetime.time:



    
    


    """Add seconds to time."""
    if time is None:
        time = datetime.datetime.now()
    if isinstance(time, datetime.time):
        time = datetime.datetime.combine(datetime.date.today(), time)
    new_time = time + datetime.timedelta(seconds=seconds)
    return new_time.time()


# Type Checking/Conversion Functions
def pb_isnull(value: Any) -> bool:

    
    
    """Check if value is null."""
    return value is None


def pb_isvalid(value: Any) -> bool:



    
    


    """Check if value is valid (not null)."""
    return value is not None


def pb_isnumber(value: str) -> bool:



    
    


    """Check if string is a valid number."""
    if value is None:
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def pb_isdate(value: str) -> bool:



    
    


    """Check if string is a valid date."""
    if value is None:
        return False
    # Try common date formats
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            datetime.datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def pb_istime(value: str) -> bool:



    
    


    """Check if string is a valid time."""
    if value is None:
        return False
    # Try common time formats
    formats = ["%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"]
    for fmt in formats:
        try:
            datetime.datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def pb_string(value: Any, format_str: str = None) -> str:



    
    


    """Convert value to string with optional format."""
    if value is None:
        return ""
    
    if format_str and isinstance(value, (int, float)):
        # Simple number formatting
        if "." in format_str:
            decimals = len(format_str.split(".")[1])
            return f"{value:.{decimals}f}"
    
    return str(value)


def pb_real(value: Any) -> float:



    
    


    """Convert to real (float)."""
    if value is None:
        return 0.0
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return 0.0
    return float(value)


def pb_double(value: Any) -> float:



    
    


    """Convert to double (same as real in Python)."""
    return pb_real(value)


def pb_integer(value: Any) -> int:



    
    


    """Convert to integer."""
    return pb_int(value)


def pb_boolean(value: Any) -> bool:



    
    


    """Convert to boolean."""
    if value is None:
        return False
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "t", "y")
    return bool(value)


def pb_date(value: str | datetime.datetime) -> datetime.date:



    
    


    """Convert to date."""
    if value is None:
        return datetime.date.today()
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        # Try common formats
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    raise ValueError(f"Cannot convert {value} to date")


def pb_time(value: str | datetime.datetime) -> datetime.time:



    
    


    """Convert to time."""
    if value is None:
        return datetime.datetime.now().time()
    if isinstance(value, datetime.datetime):
        return value.time()
    if isinstance(value, datetime.time):
        return value
    if isinstance(value, str):
        # Try common formats
        formats = ["%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(value, fmt).time()
            except ValueError:
                continue
    raise ValueError(f"Cannot convert {value} to time")


def pb_datetime(date_val: Any, time_val: Any = None) -> datetime.datetime:



    
    


    """Convert to datetime."""
    if date_val is None:
        return datetime.datetime.now()
    
    if isinstance(date_val, datetime.datetime):
        return date_val
    
    if time_val is None:
        # Single argument - parse as datetime string
        if isinstance(date_val, str):
            formats = ["%Y-%m-%d %H:%M:%S", "%m/%d/%Y %I:%M %p"]
            for fmt in formats:
                try:
                    return datetime.datetime.strptime(date_val, fmt)
                except ValueError:
                    continue
        return datetime.datetime.now()
    
    # Two arguments - combine date and time
    date = pb_date(date_val)
    time = pb_time(time_val)
    return datetime.datetime.combine(date, time)


def pb_decimal(value: Any, precision: int = 2) -> float:



    
    


    """Convert to decimal with specified precision."""
    if value is None:
        return 0.0
    result = pb_real(value)
    return round(result, precision)


# Array Functions
def pb_upperbound(array: list, dimension: int = 1) -> int:

    
    
    """Return upper bound of array (size in PowerBuilder terms)."""
    if array is None or not isinstance(array, list):
        return 0
    
    if dimension == 1:
        return len(array)
    else:
        # For multi-dimensional arrays
        if array and isinstance(array[0], list):
            return pb_upperbound(array[0], dimension - 1)
        return 0


def pb_lowerbound(array: list, dimension: int = 1) -> int:



    
    


    """Return lower bound of array (always 1 in PowerBuilder)."""
    if array is None or not isinstance(array, list):
        return 0
    return 1 if len(array) > 0 else 0


# Control Flow Functions
def pb_if(condition: bool, true_value: Any, false_value: Any) -> Any:

    
    
    """If function (ternary operator)."""
    return true_value if condition else false_value


def pb_choose(index: int, *values) -> Any:



    
    


    """Choose value based on index (1-based)."""
    if index < 1 or index > len(values):
        return None
    return values[index - 1]


def pb_case(value: Any, *case_pairs, default=None) -> Any:



    
    


    """Case function with value pairs and optional default.
    
    Usage: case(value, case1, result1, case2, result2, ..., default=default_result)
    """
    # Process pairs of (case_value, result)
    for i in range(0, len(case_pairs), 2):
        if i + 1 < len(case_pairs):
            if value == case_pairs[i]:
                return case_pairs[i + 1]
    return default