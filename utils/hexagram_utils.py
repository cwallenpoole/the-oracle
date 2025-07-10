"""
Hexagram utility functions for The Oracle application.
"""
import re
from logic import iching
from logic.iching_cache import get_hexagram_section_cached, get_all_hexagrams_cached, get_hexagram_symbols_cached


def get_all_hexagrams():
    """Get all 64 hexagrams with their basic info (cached version)"""
    hexagrams = []
    # Use cached version that loads all hexagrams at once
    all_hex_objects = get_all_hexagrams_cached()

    for i in range(1, 65):
        hex_obj = all_hex_objects.get(i)
        if hex_obj:
            hexagrams.append({
                'number': hex_obj.Number,
                'title': hex_obj.Title,
                'symbol': hex_obj.Symbol,
                'url_name': create_hexagram_url_name(hex_obj.Title),
                'description': hex_obj.About.Description[:100] + '...' if len(hex_obj.About.Description) > 100 else hex_obj.About.Description
            })
    return hexagrams


def create_hexagram_url_name(title):
    """Create URL-friendly name from hexagram title"""
    # Remove Chinese characters and extract English name
    # Pattern: "Ch'ien / The Creative" -> "the_creative"
    # Pattern: "Kuan / Contemplation (View)" -> "contemplation"

    # Split by / and take the second part (English name)
    parts = title.split('/')
    if len(parts) > 1:
        english_name = parts[1].strip()
    else:
        english_name = parts[0].strip()

    # Remove parenthetical sections
    english_name = re.sub(r'[\[(][^\])]*[\])]', '', english_name).strip()

    # Convert to lowercase, replace spaces with underscores
    # Remove any remaining special characters except underscores
    url_name = re.sub('\W+', '_', english_name).lower()

    return url_name


def parse_hexagram_url(url_path):
    """Parse hexagram URL and return number and canonical URL name"""
    # URL format: "20-contemplation" or "20-this_%38_rAnD0m"
    parts = url_path.split('-', 1)
    if len(parts) != 2:
        return None, None

    try:
        number = int(parts[0])
        if number < 1 or number > 64:
            return None, None

        # Get the canonical URL name using cached version
        hex_obj = get_hexagram_section_cached(number)
        if hex_obj:
            canonical_name = create_hexagram_url_name(hex_obj.Title)
            return number, canonical_name

        return None, None
    except ValueError:
        return None, None


def get_hexagram_symbols():
    """Get mapping of hexagram numbers to their Unicode symbols (cached version)"""
    # Use the cached symbols method for much better performance
    return get_hexagram_symbols_cached()
