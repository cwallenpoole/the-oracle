"""
Calendar conversion utilities for The Oracle application.

Provides functions to convert Gregorian dates to:
- Chinese zodiac years and animals
- Mayan Tzolk'in, Haab, and Long Count calendars
"""

from datetime import datetime, date
from typing import Dict, Tuple, Union

# Chinese Zodiac animals in order
CHINESE_ZODIAC_ANIMALS = [
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"
]

# Chinese New Year dates for recent years (approximation - in practice, this would be a larger lookup table)
CHINESE_NEW_YEAR_DATES = {
    2020: (2020, 1, 25),   # Rat
    2021: (2021, 2, 12),   # Ox
    2022: (2022, 2, 1),    # Tiger
    2023: (2023, 1, 22),   # Rabbit
    2024: (2024, 2, 10),   # Dragon
    2025: (2025, 1, 29),   # Snake
    2026: (2026, 2, 17),   # Horse
    2027: (2027, 2, 6),    # Goat
    2028: (2028, 1, 26),   # Monkey
    2029: (2029, 2, 13),   # Rooster
    2030: (2030, 2, 3),    # Dog
    2031: (2031, 1, 23),   # Pig
}

# Mayan Tzolk'in day names (20 days)
TZOLKIN_DAY_NAMES = [
    "Imix", "Ik", "Akbal", "Kan", "Chicchan", "Cimi", "Manik", "Lamat",
    "Muluk", "Ok", "Chuen", "Eb", "Ben", "Ix", "Men", "Cib",
    "Caban", "Eznab", "Cauac", "Ahau"
]

# Mayan Haab month names (18 months + Wayeb)
HAAB_MONTH_NAMES = [
    "Pop", "Wo", "Sip", "Sotz", "Sek", "Xul", "Yaxkin", "Mol",
    "Chen", "Yax", "Sak", "Keh", "Mak", "Kankin", "Muan", "Pax",
    "Kayab", "Kumku", "Wayeb"
]

# Long Count correlation constant (days between Mayan creation date and Gregorian calendar)
# Using the GMT correlation: August 11, 3114 BCE (proleptic Gregorian) = 0.0.0.0.0
LONG_COUNT_CORRELATION = 584283  # Julian Day Number of Mayan creation date


def get_chinese_year_and_animal(year: int, month: int, day: int) -> Dict[str, Union[int, str]]:
    """
    Convert a Gregorian date to Chinese zodiac year and animal.

    Args:
        year: Gregorian year
        month: Month (1-12)
        day: Day of month (1-31)

    Returns:
        Dictionary containing:
        - 'chinese_year': The Chinese calendar year
        - 'animal': The zodiac animal name
        - 'element': The associated element (Wood, Fire, Earth, Metal, Water)
        - 'yin_yang': Whether it's a Yin or Yang year
    """
    input_date = date(year, month, day)

    # Determine which Chinese year this date falls into
    chinese_year = year

    # Check if we have the Chinese New Year date for this year
    if year in CHINESE_NEW_YEAR_DATES:
        new_year_date = date(*CHINESE_NEW_YEAR_DATES[year])
        if input_date < new_year_date:
            chinese_year = year - 1
    elif year - 1 in CHINESE_NEW_YEAR_DATES:
        # Check previous year's new year date
        prev_new_year = date(*CHINESE_NEW_YEAR_DATES[year - 1])
        if input_date < prev_new_year:
            chinese_year = year - 2
    else:
        # Approximate Chinese New Year (usually late January to mid February)
        # This is a rough approximation - for exact dates, a comprehensive lookup table would be needed
        estimated_new_year = date(year, 2, 1)  # Rough estimate
        if input_date < estimated_new_year:
            chinese_year = year - 1

    # Calculate zodiac animal (12-year cycle, starting with Rat in 1924)
    animal_index = (chinese_year - 1924) % 12
    animal = CHINESE_ZODIAC_ANIMALS[animal_index]

    # Calculate element (5-element cycle: Wood, Fire, Earth, Metal, Water)
    elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
    element_index = ((chinese_year - 1924) // 2) % 5
    element = elements[element_index]

    # Determine Yin/Yang (even years are Yang, odd years are Yin in the cycle)
    yin_yang = "Yang" if (chinese_year - 1924) % 2 == 0 else "Yin"

    return {
        'chinese_year': chinese_year,
        'animal': animal,
        'element': element,
        'yin_yang': yin_yang
    }


def gregorian_to_julian_day(year: int, month: int, day: int) -> int:
    """
    Convert Gregorian date to Julian Day Number.

    Args:
        year: Gregorian year
        month: Month (1-12)
        day: Day of month (1-31)

    Returns:
        Julian Day Number
    """
    # Handle BCE years
    if year < 1:
        year = year - 1

    if month <= 2:
        year -= 1
        month += 12

    # Gregorian calendar correction
    a = year // 100
    b = 2 - a + (a // 4)

    # Julian Day calculation
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524

    return jd


def get_mayan_calendars(year: int, month: int, day: int) -> Dict[str, Union[str, int, Dict]]:
    """
    Convert a Gregorian date to Mayan calendar systems.

    Args:
        year: Gregorian year
        month: Month (1-12)
        day: Day of month (1-31)

    Returns:
        Dictionary containing:
        - 'tzolkin': Tzolk'in calendar date (sacred 260-day calendar)
        - 'haab': Haab calendar date (365-day solar calendar)
        - 'long_count': Long Count calendar date
        - 'lord_of_night': Lord of the Night (G1-G9)
    """
    julian_day = gregorian_to_julian_day(year, month, day)

    # Calculate days since Mayan creation date
    days_since_creation = julian_day - LONG_COUNT_CORRELATION

    # Tzolk'in calculation (260-day cycle)
    tzolkin_number = ((days_since_creation - 159) % 13) + 1
    tzolkin_day_index = (days_since_creation - 159) % 20
    tzolkin_day_name = TZOLKIN_DAY_NAMES[tzolkin_day_index]

    # Haab calculation (365-day cycle)
    haab_day_in_year = (days_since_creation - 348) % 365
    haab_month_index = haab_day_in_year // 20
    haab_day = haab_day_in_year % 20

    if haab_month_index < 18:
        haab_month = HAAB_MONTH_NAMES[haab_month_index]
    else:
        haab_month = "Wayeb"
        haab_day = haab_day_in_year - 360  # Wayeb days are 0-4

    # Long Count calculation
    long_count_days = days_since_creation

    # Long Count units: 1 kin = 1 day, 1 winal = 20 kin, 1 tun = 18 winal, 1 katun = 20 tun, 1 baktun = 20 katun
    baktun = long_count_days // 144000
    remaining = long_count_days % 144000

    katun = remaining // 7200
    remaining = remaining % 7200

    tun = remaining // 360
    remaining = remaining % 360

    winal = remaining // 20
    kin = remaining % 20

    # Lord of the Night (G1-G9, 9-day cycle)
    lord_of_night = ((days_since_creation % 9) + 1)

    return {
        'tzolkin': {
            'number': tzolkin_number,
            'day_name': tzolkin_day_name,
            'formatted': f"{tzolkin_number} {tzolkin_day_name}"
        },
        'haab': {
            'day': haab_day,
            'month': haab_month,
            'formatted': f"{haab_day} {haab_month}"
        },
        'long_count': {
            'baktun': baktun,
            'katun': katun,
            'tun': tun,
            'winal': winal,
            'kin': kin,
            'formatted': f"{baktun}.{katun}.{tun}.{winal}.{kin}"
        },
        'lord_of_night': f"G{lord_of_night}"
    }


def get_chinese_and_mayan_date(year: int, month: int, day: int) -> Dict[str, Dict]:
    """
    Convenience function to get both Chinese and Mayan calendar information for a date.

    Args:
        year: Gregorian year
        month: Month (1-12)
        day: Day of month (1-31)

    Returns:
        Dictionary containing both 'chinese' and 'mayan' calendar information
    """
    return {
        'gregorian': {
            'year': year,
            'month': month,
            'day': day,
            'formatted': f"{year}-{month:02d}-{day:02d}"
        },
        'chinese': get_chinese_year_and_animal(year, month, day),
        'mayan': get_mayan_calendars(year, month, day)
    }


# Example usage and testing
if __name__ == "__main__":
    # Test with some sample dates
    test_dates = [
        (2024, 1, 1),   # New Year's Day 2024
        (2024, 2, 10),  # Chinese New Year 2024
        (2024, 12, 21), # Winter Solstice 2024
        (2012, 12, 21), # End of Mayan Long Count cycle
    ]

    for test_year, test_month, test_day in test_dates:
        print(f"\n=== {test_year}-{test_month:02d}-{test_day:02d} ===")

        chinese = get_chinese_year_and_animal(test_year, test_month, test_day)
        print(f"Chinese: {chinese['chinese_year']} - Year of the {chinese['element']} {chinese['animal']} ({chinese['yin_yang']})")

        mayan = get_mayan_calendars(test_year, test_month, test_day)
        print(f"Tzolk'in: {mayan['tzolkin']['formatted']}")
        print(f"Haab: {mayan['haab']['formatted']}")
        print(f"Long Count: {mayan['long_count']['formatted']}")
        print(f"Lord of Night: {mayan['lord_of_night']}")
