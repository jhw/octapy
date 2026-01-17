"""
Utility functions and mappings for the Octatrack API.
"""

from .enums import TrigCondition


# Mapping from probability TrigConditions to float values
PROBABILITY_MAP = {
    TrigCondition.PERCENT_1: 0.01,
    TrigCondition.PERCENT_2: 0.02,
    TrigCondition.PERCENT_4: 0.04,
    TrigCondition.PERCENT_6: 0.06,
    TrigCondition.PERCENT_9: 0.09,
    TrigCondition.PERCENT_13: 0.13,
    TrigCondition.PERCENT_19: 0.19,
    TrigCondition.PERCENT_25: 0.25,
    TrigCondition.PERCENT_33: 0.33,
    TrigCondition.PERCENT_41: 0.41,
    TrigCondition.PERCENT_50: 0.50,
    TrigCondition.PERCENT_59: 0.59,
    TrigCondition.PERCENT_67: 0.67,
    TrigCondition.PERCENT_75: 0.75,
    TrigCondition.PERCENT_81: 0.81,
    TrigCondition.PERCENT_87: 0.87,
    TrigCondition.PERCENT_91: 0.91,
    TrigCondition.PERCENT_94: 0.94,
    TrigCondition.PERCENT_96: 0.96,
    TrigCondition.PERCENT_98: 0.98,
    TrigCondition.PERCENT_99: 0.99,
}
