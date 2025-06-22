"""A simple script to verify that imports work correctly."""

import os
import sys

# Print the Python version

# Print pytest version

# Print Lark version

# Print sys.path
for _path in sys.path:
    pass

# Check if our package directories are accessible
for package in [
    "parse",
    "model",
    "extract",
    "decompile",
    "generate",
    "output",
    "reference",
]:
    if os.path.exists(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), package),
    ):
        pass
    else:
        pass
