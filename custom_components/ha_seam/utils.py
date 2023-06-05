"""Utility functions for the Home Assistant SEAM integration."""

import re

NAME_PATTERN = re.compile(r"\w+")

def normalize_name(string) -> str:
    """Normalize a string to a valid entity name."""
    return "_".join(NAME_PATTERN.findall(str(string).lower()))
