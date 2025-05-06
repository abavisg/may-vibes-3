"""
Constants used throughout the Smart Inbox Cleaner application
"""

# Categorization methods
CAT_METHOD_LLM = "LLM Categorization"
CAT_METHOD_RULES = "Rule-Based Categorization"

# Category constants (imported from categorizer.py)
from categorizer import (
    CAT_ACTION,
    CAT_READ,
    CAT_EVENTS,
    CAT_INFO,
    CAT_UNCATEGORISED,
    MOVE_CATEGORIES,
    RULE_CATEGORIES
) 