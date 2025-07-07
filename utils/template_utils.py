"""
Template utility functions and filters for The Oracle application.
"""
import re
import markdown
from flask import url_for
from logic import iching
from utils.hexagram_utils import create_hexagram_url_name


def enhance_reading_with_links(reading_text):
    """Enhance reading text by adding links to hexagrams and styling transitions"""
    if not reading_text:
        return reading_text

    # Pattern to match hexagram references like "Hexagram 20" or "20: Kuan"
    def replace_hexagram_ref(match):
        number = int(match.group(1))
        if 1 <= number <= 64:
            hex_obj = iching.get_hexagram_section(number)
            if hex_obj:
                url_name = create_hexagram_url_name(hex_obj.Title)
                return f'<a href="{url_for("nav.hexagram_detail", number=number, name=url_name)}" class="hexagram-link">{hex_obj.Number}: {hex_obj.Title}</a>'
        return match.group(0)

    # Replace patterns like "Hexagram 20", "hexagram 20", "20: Title"
    enhanced = re.sub(r'[Hh]exagram (\d+)', replace_hexagram_ref, reading_text)
    enhanced = re.sub(r'(\d+):\s*[A-Za-z\']+', replace_hexagram_ref, enhanced)

    return enhanced


def sanitize_css_selector(text):
    """Convert trigram text to a valid CSS selector ID that matches the trigram list"""
    if not text:
        return ""

    # Mapping from hexagram trigram descriptions to trigram IDs
    trigram_mapping = {
        "ch'ien": "heaven",
        "chien": "heaven",
        "k'un": "earth",
        "kun": "earth",
        "chen": "thunder",
        "k'an": "water",
        "kan": "water",
        "ken": "mountain",
        "kên": "mountain",  # Handle accent
        "sun": "wind",
        "li": "fire",
        "tui": "lake"
    }

    # Extract the first word and clean it
    first_word = text.split()[0].lower()
    # Remove apostrophes and special characters
    clean_word = re.sub(r"[^a-z0-9]", "", first_word)

    # Check if it maps to a known trigram
    if clean_word in trigram_mapping:
        return trigram_mapping[clean_word]

    # If we find "heaven", "earth", etc. in the text, use those directly
    text_lower = text.lower()
    for keyword in ["heaven", "earth", "thunder", "water", "mountain", "wind", "fire", "lake"]:
        if keyword in text_lower:
            return keyword

    # Fallback: return the cleaned first word
    return clean_word


def markdown_filter(text):
    """Convert markdown text to HTML"""
    if not text:
        return ""
    return markdown.markdown(text)


def extract_followup_question(request_data):
    """Extract the follow-up question from LLM request data"""
    if not request_data:
        return "Follow-up question"

    # Look for the pattern: follow-up question: "question text"
    match = re.search(r'follow-up question: "([^"]*)"', request_data)
    if match:
        return match.group(1)

    # Fallback: look for any quoted text after "follow-up"
    match = re.search(r'follow-up[^"]*"([^"]*)"', request_data, re.IGNORECASE)
    if match:
        return match.group(1)

    return "Follow-up question"


def clean_question_filter(text):
    """Clean question text by removing code blocks and stripping lines"""
    if not text:
        return ""

    # Remove code block markers
    text = text.replace('```', '')

    # Split into lines, strip each line, and rejoin
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines]

    # Remove empty lines at the beginning and end
    while cleaned_lines and not cleaned_lines[0]:
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1]:
        cleaned_lines.pop()

    return '\n'.join(cleaned_lines)


def register_template_filters(app):
    """Register all template filters with the Flask app"""
    app.jinja_env.filters['sanitize_css_selector'] = sanitize_css_selector
    app.jinja_env.filters['markdown'] = markdown_filter
    app.jinja_env.filters['extract_followup_question'] = extract_followup_question
    app.jinja_env.filters['clean_question'] = clean_question_filter
