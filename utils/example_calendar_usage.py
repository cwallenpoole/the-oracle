#!/usr/bin/env python3
"""
Example usage of the calendar utility functions.
Demonstrates how to convert dates to Chinese zodiac and Mayan calendars.
"""

from utils.calendar_utils import (
    get_chinese_year_and_animal,
    get_mayan_calendars,
    get_chinese_and_mayan_date
)

def main():
    print("=== Calendar Conversion Examples ===\n")

    # Example dates
    example_dates = [
        (2024, 1, 1, "New Year's Day 2024"),
        (2024, 2, 10, "Chinese New Year 2024 (Dragon Year)"),
        (2012, 12, 21, "End of Mayan Long Count Cycle"),
        (1969, 7, 20, "Moon Landing"),
        (2000, 1, 1, "Y2K - New Millennium"),
        (1776, 7, 4, "American Independence"),
        (2023, 12, 25, "Christmas 2023"),
    ]

    for year, month, day, description in example_dates:
        print(f"📅 {description} ({year}-{month:02d}-{day:02d})")
        print("-" * 50)

        # Get Chinese zodiac information
        chinese = get_chinese_year_and_animal(year, month, day)
        print(f"🐉 Chinese: {chinese['chinese_year']} - Year of the {chinese['element']} {chinese['animal']} ({chinese['yin_yang']})")

        # Get Mayan calendar information
        mayan = get_mayan_calendars(year, month, day)
        print(f"🏛️  Mayan Calendars:")
        print(f"   • Tzolk'in: {mayan['tzolkin']['formatted']} (Sacred 260-day calendar)")
        print(f"   • Haab: {mayan['haab']['formatted']} (365-day solar calendar)")
        print(f"   • Long Count: {mayan['long_count']['formatted']}")
        print(f"   • Lord of Night: {mayan['lord_of_night']}")
        print()

def interactive_demo():
    """Interactive demonstration where user can input their own dates."""
    print("=== Interactive Calendar Converter ===\n")

    try:
        year = int(input("Enter year (e.g., 2024): "))
        month = int(input("Enter month (1-12): "))
        day = int(input("Enter day (1-31): "))

        print(f"\n📅 Converting {year}-{month:02d}-{day:02d}...")
        print("=" * 50)

        # Get all calendar information at once
        calendar_info = get_chinese_and_mayan_date(year, month, day)

        print(f"🌍 Gregorian: {calendar_info['gregorian']['formatted']}")
        print()

        chinese = calendar_info['chinese']
        print(f"🐉 Chinese Calendar:")
        print(f"   • Year: {chinese['chinese_year']}")
        print(f"   • Animal: {chinese['animal']}")
        print(f"   • Element: {chinese['element']}")
        print(f"   • Yin/Yang: {chinese['yin_yang']}")
        print()

        mayan = calendar_info['mayan']
        print(f"🏛️  Mayan Calendars:")
        print(f"   • Tzolk'in: {mayan['tzolkin']['formatted']}")
        print(f"   • Haab: {mayan['haab']['formatted']}")
        print(f"   • Long Count: {mayan['long_count']['formatted']}")
        print(f"   • Lord of Night: {mayan['lord_of_night']}")

    except ValueError:
        print("Please enter valid numbers for year, month, and day.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

    # Ask if user wants to try interactive mode
    while True:
        try_interactive = input("\nWould you like to try the interactive converter? (y/n): ").lower()
        if try_interactive == 'y':
            interactive_demo()
            break
        elif try_interactive == 'n':
            print("Thanks for using the calendar converter!")
            break
        else:
            print("Please enter 'y' for yes or 'n' for no.")
