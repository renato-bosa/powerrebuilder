"""PowerBuilder system functions.

This module defines classes and functions for PowerBuilder system functions
and built-in functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from model.utils.base import PBNode


# Function category enum
class PBFunctionCategory(Enum):
    """Categories for PowerBuilder system functions."""

    STRING = auto()
    MATH = auto()
    DATE = auto()
    TIME = auto()
    CONVERSION = auto()
    SYSTEM = auto()
    UI = auto()
    DATABASE = auto()
    FILE = auto()
    ARRAY = auto()
    OBJECT = auto()
    OTHER = auto()


@dataclass
class PBParameter:
    """Function parameter definition."""

    name: str
    type_name: str
    is_optional: bool = False
    default_value: Any | None = None
    is_reference: bool = False
    is_readonly: bool = False
    description: str | None = None


@dataclass
class PBBuiltInFunction(PBNode):
    """PowerBuilder built-in function base class."""

    name: str
    category: PBFunctionCategory
    return_type: str
    parameters: list[PBParameter] = field(default_factory=list)
    description: str | None = None
    examples: list[str] = field(default_factory=list)


@dataclass
class PBSystemFunction(PBBuiltInFunction):
    """PowerBuilder system function."""

    is_deprecated: bool = False
    alternative: str | None = None
    version_introduced: str | None = None
    version_deprecated: str | None = None


# Registry for system functions
_SYSTEM_FUNCTIONS: dict[str, PBSystemFunction] = {}


def register_system_function(func: PBSystemFunction) -> PBSystemFunction:








    """Register a system function.

    Args:
        func: The function to register

    Returns:
        The registered function

    Raises:
        ValueError: If a function with the same name already exists
    """
    func_name_lower = func.name.lower()
    if func_name_lower in _SYSTEM_FUNCTIONS:
        msg = f"Function {func.name} already registered"
        raise ValueError(msg)

    _SYSTEM_FUNCTIONS[func_name_lower] = func
    return func


def get_system_function(name: str) -> PBSystemFunction | None:








    """Get a system function by name.

    Args:
        name: The name of the function (case-insensitive)

    Returns:
        The function, or None if not found
    """
    return _SYSTEM_FUNCTIONS.get(name.lower())


def get_system_functions_by_category(
    category: PBFunctionCategory, ) -> list[PBSystemFunction]:








    """Get all system functions in a category.

    Args:
        category: The category to filter by

    Returns:
        List of functions in the category
    """
    return [func for func in _SYSTEM_FUNCTIONS.values() if func.category == category]


def get_all_system_functions() -> list[PBSystemFunction]:








    """Get all registered system functions.

    Returns:
        List of all system functions
    """
    return list(_SYSTEM_FUNCTIONS.values())


# Register common PowerBuilder system functions

# String functions
register_system_function(
    PBSystemFunction(
        name="Len", category=PBFunctionCategory.STRING, return_type="integer", parameters=[
            PBParameter(name="string", type_name="string"), ], description="Returns the length of a string", examples=["len('Hello World') // Returns 11"], ), )

register_system_function(
    PBSystemFunction(
        name="Left", category=PBFunctionCategory.STRING, return_type="string", parameters=[
            PBParameter(name="string", type_name="string"), PBParameter(name="length", type_name="integer"), ], description="Returns the leftmost n characters of a string", examples=["Left('Hello World', 5) // Returns 'Hello'"], ), )

register_system_function(
    PBSystemFunction(
        name="Right", category=PBFunctionCategory.STRING, return_type="string", parameters=[
            PBParameter(name="string", type_name="string"), PBParameter(name="length", type_name="integer"), ], description="Returns the rightmost n characters of a string", examples=["Right('Hello World', 5) // Returns 'World'"], ), )

register_system_function(
    PBSystemFunction(
        name="Mid", category=PBFunctionCategory.STRING, return_type="string", parameters=[
            PBParameter(name="string", type_name="string"), PBParameter(name="start", type_name="integer"), PBParameter(name="length", type_name="integer", is_optional=True), ], description="Returns a substring from a string", examples=[
            "Mid('Hello World', 7) // Returns 'World'", "Mid('Hello World', 7, 3) // Returns 'Wor'", ], ), )

register_system_function(
    PBSystemFunction(
        name="Trim", category=PBFunctionCategory.STRING, return_type="string", parameters=[
            PBParameter(name="string", type_name="string"), ], description="Removes leading and trailing spaces from a string", examples=["Trim('  Hello  ') // Returns 'Hello'"], ), )

register_system_function(
    PBSystemFunction(
        name="Upper", category=PBFunctionCategory.STRING, return_type="string", parameters=[
            PBParameter(name="string", type_name="string"), ], description="Converts a string to uppercase", examples=["Upper('Hello') // Returns 'HELLO'"], ), )

register_system_function(
    PBSystemFunction(
        name="Lower", category=PBFunctionCategory.STRING, return_type="string", parameters=[
            PBParameter(name="string", type_name="string"), ], description="Converts a string to lowercase", examples=["Lower('Hello') // Returns 'hello'"], ), )

register_system_function(
    PBSystemFunction(
        name="Pos", category=PBFunctionCategory.STRING, return_type="integer", parameters=[
            PBParameter(name="substring", type_name="string"), PBParameter(name="string", type_name="string"), PBParameter(name="start", type_name="integer", is_optional=True), ], description="Finds the position of a substring in a string", examples=[
            "Pos('o', 'Hello World') // Returns 5", "Pos('o', 'Hello World', 6) // Returns 8", ], ), )

register_system_function(
    PBSystemFunction(
        name="Replace", category=PBFunctionCategory.STRING, return_type="string", parameters=[
            PBParameter(name="string", type_name="string"), PBParameter(name="start", type_name="integer"), PBParameter(name="length", type_name="integer"), PBParameter(name="replacement", type_name="string"), ], description="Replaces a portion of a string with another string", examples=[
            "Replace('Hello World', 7, 5, 'Universe') // Returns 'Hello Universe'", ], ), )

# Math functions
register_system_function(
    PBSystemFunction(
        name="Abs", category=PBFunctionCategory.MATH, return_type="double", parameters=[
            PBParameter(name="value", type_name="double"), ], description="Returns the absolute value of a number", examples=["Abs(-5.7) // Returns 5.7"], ), )

register_system_function(
    PBSystemFunction(
        name="Ceiling", category=PBFunctionCategory.MATH, return_type="double", parameters=[
            PBParameter(name="value", type_name="double"), ], description="Returns the smallest integer greater than or equal to a number", examples=["Ceiling(5.7) // Returns 6.0"], ), )

register_system_function(
    PBSystemFunction(
        name="Floor", category=PBFunctionCategory.MATH, return_type="double", parameters=[
            PBParameter(name="value", type_name="double"), ], description="Returns the largest integer less than or equal to a number", examples=["Floor(5.7) // Returns 5.0"], ), )

register_system_function(
    PBSystemFunction(
        name="Round", category=PBFunctionCategory.MATH, return_type="double", parameters=[
            PBParameter(name="value", type_name="double"), PBParameter(name="decimals", type_name="integer", is_optional=True), ], description="Rounds a number to a specified number of decimal places", examples=[
            "Round(5.75) // Returns 6.0", "Round(5.75, 1) // Returns 5.8", ], ), )

register_system_function(
    PBSystemFunction(
        name="Sqrt", category=PBFunctionCategory.MATH, return_type="double", parameters=[
            PBParameter(name="value", type_name="double"), ], description="Returns the square root of a number", examples=["Sqrt(16) // Returns 4.0"], ), )

register_system_function(
    PBSystemFunction(
        name="Mod", category=PBFunctionCategory.MATH, return_type="integer", parameters=[
            PBParameter(name="dividend", type_name="integer"), PBParameter(name="divisor", type_name="integer"), ], description="Returns the remainder after division", examples=["Mod(10, 3) // Returns 1"], ), )

register_system_function(
    PBSystemFunction(
        name="Truncate", category=PBFunctionCategory.MATH, return_type="double", parameters=[
            PBParameter(name="value", type_name="double"), PBParameter(name="decimals", type_name="integer", is_optional=True), ], description="Truncates a number to a specified number of decimal places", examples=[
            "Truncate(5.75) // Returns 5.0", "Truncate(5.75, 1) // Returns 5.7", ], ), )

# Date and Time functions
register_system_function(
    PBSystemFunction(
        name="Today", category=PBFunctionCategory.DATE, return_type="date", parameters=[], description="Returns the current date", examples=["Today() // Returns current system date"], ), )

register_system_function(
    PBSystemFunction(
        name="Now", category=PBFunctionCategory.TIME, return_type="datetime", parameters=[], description="Returns the current date and time", examples=["Now() // Returns current system date and time"], ), )

register_system_function(
    PBSystemFunction(
        name="Day", category=PBFunctionCategory.DATE, return_type="integer", parameters=[
            PBParameter(name="date", type_name="date"), ], description="Returns the day of the month from a date", examples=["Day(Date('2023-05-15')) // Returns 15"], ), )

register_system_function(
    PBSystemFunction(
        name="Month", category=PBFunctionCategory.DATE, return_type="integer", parameters=[
            PBParameter(name="date", type_name="date"), ], description="Returns the month from a date", examples=["Month(Date('2023-05-15')) // Returns 5"], ), )

register_system_function(
    PBSystemFunction(
        name="Year", category=PBFunctionCategory.DATE, return_type="integer", parameters=[
            PBParameter(name="date", type_name="date"), ], description="Returns the year from a date", examples=["Year(Date('2023-05-15')) // Returns 2023"], ), )

register_system_function(
    PBSystemFunction(
        name="DaysAfter", category=PBFunctionCategory.DATE, return_type="date", parameters=[
            PBParameter(name="date", type_name="date"), PBParameter(name="days", type_name="integer"), ], description="Returns a date that is a specified number of days after a date", examples=["DaysAfter(Date('2023-05-15'), 10) // Returns 2023-05-25"], ), )

# UI functions
register_system_function(
    PBSystemFunction(
        name="MessageBox", category=PBFunctionCategory.UI, return_type="integer", parameters=[
            PBParameter(name="title", type_name="string"), PBParameter(name="text", type_name="string"), PBParameter(name="icon", type_name="integer", is_optional=True), PBParameter(name="button", type_name="integer", is_optional=True), PBParameter(name="default", type_name="integer", is_optional=True), ], description="Displays a message box with specified options", examples=[
            "MessageBox('Warning', 'Data not saved!', Exclamation!, OKCancel!, 1) // Displays warning message", ], ), )

# File functions
register_system_function(
    PBSystemFunction(
        name="FileExists", category=PBFunctionCategory.FILE, return_type="boolean", parameters=[
            PBParameter(name="filename", type_name="string"), ], description="Checks if a file exists", examples=["FileExists('C:\\data.txt') // Returns true if file exists"], ), )

register_system_function(
    PBSystemFunction(
        name="FileOpen", category=PBFunctionCategory.FILE, return_type="integer", parameters=[
            PBParameter(name="filename", type_name="string"), PBParameter(name="mode", type_name="integer"), ], description="Opens a file for reading or writing", examples=["FileOpen('data.txt', TextMode!) // Opens text file"], ), )

register_system_function(
    PBSystemFunction(
        name="FileClose", category=PBFunctionCategory.FILE, return_type="integer", parameters=[
            PBParameter(name="file_handle", type_name="integer"), ], description="Closes an open file", examples=["FileClose(1) // Closes file with handle 1"], ), )

register_system_function(
    PBSystemFunction(
        name="FileRead", category=PBFunctionCategory.FILE, return_type="integer", parameters=[
            PBParameter(name="file_handle", type_name="integer"), PBParameter(name="buffer", type_name="string", is_reference=True), ], description="Reads data from an open file", examples=["FileRead(1, ls_data) // Reads data into ls_data"], ), )

register_system_function(
    PBSystemFunction(
        name="FileWrite", category=PBFunctionCategory.FILE, return_type="integer", parameters=[
            PBParameter(name="file_handle", type_name="integer"), PBParameter(name="data", type_name="string"), ], description="Writes data to an open file", examples=["FileWrite(1, 'Hello World') // Writes string to file"], ), )

# System functions
register_system_function(
    PBSystemFunction(
        name="GetEnvironment", category=PBFunctionCategory.SYSTEM, return_type="integer", parameters=[
            PBParameter(name="name", type_name="string"), PBParameter(name="value", type_name="string", is_reference=True), ], description="Gets the value of an environment variable", examples=["GetEnvironment('PATH', ls_path) // Gets PATH environment variable"], ), )

register_system_function(
    PBSystemFunction(
        name="GetComputerName", category=PBFunctionCategory.SYSTEM, return_type="string", parameters=[], description="Gets the name of the computer", examples=["GetComputerName() // Returns computer name"], ), )

register_system_function(
    PBSystemFunction(
        name="GetUserName", category=PBFunctionCategory.SYSTEM, return_type="string", parameters=[], description="Gets the name of the current user", examples=["GetUserName() // Returns current user name"], ), )

# Object functions
register_system_function(
    PBSystemFunction(
        name="IsValid", category=PBFunctionCategory.OBJECT, return_type="boolean", parameters=[
            PBParameter(name="object", type_name="powerobject"), ], description="Determines whether an object reference is valid", examples=["IsValid(w_main) // Returns true if w_main is valid"], ), )

register_system_function(
    PBSystemFunction(
        name="ClassName", category=PBFunctionCategory.OBJECT, return_type="string", parameters=[
            PBParameter(name="object", type_name="powerobject"), ], description="Returns the class name of an object", examples=["ClassName(w_main) // Returns 'w_main'"], ), )

register_system_function(
    PBSystemFunction(
        name="TypeOf", category=PBFunctionCategory.OBJECT, return_type="integer", parameters=[
            PBParameter(name="object", type_name="powerobject"), PBParameter(name="type_name", type_name="string"), ], description="Determines whether an object is of a specific type", examples=["TypeOf(w_main, 'window') // Returns 1 if w_main is a window"], ), )

# Array functions
register_system_function(
    PBSystemFunction(
        name="UpperBound", category=PBFunctionCategory.ARRAY, return_type="integer", parameters=[
            PBParameter(name="array", type_name="any"), PBParameter(name="dimension", type_name="integer", is_optional=True), ], description="Returns the upper bound of an array", examples=[
            "UpperBound(la_data) // Returns the upper bound of la_data's first dimension", "UpperBound(la_data, 2) // Returns the upper bound of la_data's second dimension", ], ), )

register_system_function(
    PBSystemFunction(
        name="Sort", category=PBFunctionCategory.ARRAY, return_type="integer", parameters=[
            PBParameter(name="array", type_name="any", is_reference=True), PBParameter(name="begin", type_name="integer", is_optional=True), PBParameter(name="end", type_name="integer", is_optional=True), ], description="Sorts an array", examples=[
            "Sort(la_data) // Sorts the entire array", "Sort(la_data, 1, 10) // Sorts elements 1 through 10", ], ), )

# Conversion functions
register_system_function(
    PBSystemFunction(
        name="String", category=PBFunctionCategory.CONVERSION, return_type="string", parameters=[
            PBParameter(name="value", type_name="any"), PBParameter(name="format", type_name="string", is_optional=True), ], description="Converts a value to a string", examples=[
            "String(123) // Returns '123'", "String(123.45, '#, ##0.00') // Returns '123.45'", ], ), )

register_system_function(
    PBSystemFunction(
        name="Integer", category=PBFunctionCategory.CONVERSION, return_type="integer", parameters=[
            PBParameter(name="value", type_name="any"), ], description="Converts a value to an integer", examples=["Integer('123') // Returns 123"], ), )

register_system_function(
    PBSystemFunction(
        name="Real", category=PBFunctionCategory.CONVERSION, return_type="real", parameters=[
            PBParameter(name="value", type_name="any"), ], description="Converts a value to a real number", examples=["Real('123.45') // Returns 123.45"], ), )

register_system_function(
    PBSystemFunction(
        name="Double", category=PBFunctionCategory.CONVERSION, return_type="double", parameters=[
            PBParameter(name="value", type_name="any"), ], description="Converts a value to a double-precision number", examples=["Double('123.45') // Returns 123.45"], ), )

register_system_function(
    PBSystemFunction(
        name="Date", category=PBFunctionCategory.CONVERSION, return_type="date", parameters=[
            PBParameter(name="string", type_name="string"), ], description="Converts a string to a date", examples=["Date('2023-05-15') // Returns date value for May 15, 2023"], ), )

register_system_function(
    PBSystemFunction(
        name="DateTime", category=PBFunctionCategory.CONVERSION, return_type="datetime", parameters=[
            PBParameter(name="string", type_name="string"), ], description="Converts a string to a datetime", examples=["DateTime('2023-05-15 14:30:00') // Returns datetime value"], ), )

# Database functions
register_system_function(
    PBSystemFunction(
        name="SQLCA", category=PBFunctionCategory.DATABASE, return_type="transaction", parameters=[], description="Returns a reference to the default transaction object", examples=["SQLCA.SQLCode // Gets SQL code from default transaction"], ), )

register_system_function(
    PBSystemFunction(
        name="DBError", category=PBFunctionCategory.DATABASE, return_type="integer", parameters=[
            PBParameter(name="transaction", type_name="transaction"), ], description="Returns the database error code from a transaction", examples=["DBError(SQLCA) // Returns database error code"], ), )

register_system_function(
    PBSystemFunction(
        name="SQLStringConnect", category=PBFunctionCategory.DATABASE, return_type="integer", parameters=[
            PBParameter(name="transaction", type_name="transaction"), PBParameter(name="connect_string", type_name="string"), ], description="Connects to a database using a connection string", examples=[
            "SQLStringConnect(SQLCA, 'DSN=MyDBUID=sa;PWD=password') // Connects to database",
        ],
    ),
)

# Add more system functions as needed
