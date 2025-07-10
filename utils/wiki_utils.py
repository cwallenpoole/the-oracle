"""
Wiki utilities for managing character and event wiki entries.
"""

import os
import re
import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
import markdown

# Import for AI generation
import openai
from logic.ai_readers import generate_text_with_llm

# Base wiki directory
WIKI_DIR = Path("wiki")

# Synonyms file
SYNONYMS_FILE = WIKI_DIR / "synonyms.json"

class WikiEntry:
    """Represents a wiki entry for a character, event, place, or concept"""

    def __init__(self, name: str, category: str = "characters"):
        self.name = name
        self.category = category
        self.filename = self._create_filename(name)
        self.filepath = WIKI_DIR / category / f"{self.filename}.md"

    def _create_filename(self, name: str) -> str:
        """Create a safe filename from a name"""
        # Remove brackets and clean up the name
        clean_name = re.sub(r'[^\w\s-]', '', name.strip())
        # Convert to lowercase and replace spaces with underscores
        filename = clean_name.lower().replace(' ', '_')
        return filename

    def exists(self) -> bool:
        """Check if the wiki entry file exists"""
        return self.filepath.exists()

    def is_placeholder(self) -> bool:
        """Check if the entry is just a placeholder"""
        if not self.exists():
            return True
        content = self.read_content()
        return "information not available yet" in content.lower()

    def read_content(self) -> str:
        """Read the content of the wiki entry"""
        if not self.exists():
            return ""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading wiki entry {self.filepath}: {e}")
            return ""

    def write_content(self, content: str, is_placeholder: bool = False) -> bool:
        """Write content to the wiki entry"""
        try:
            # Ensure directory exists
            self.filepath.parent.mkdir(parents=True, exist_ok=True)

            # Add metadata to the content
            metadata = f"# {self.name}\n\n"
            if is_placeholder:
                metadata += f"*Status: Placeholder - Created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            else:
                metadata += f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"

            full_content = metadata + content

            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            return True
        except Exception as e:
            print(f"Error writing wiki entry {self.filepath}: {e}")
            return False

    def create_placeholder(self) -> bool:
        """Create a placeholder wiki entry"""
        placeholder_content = f"Information not available yet.\n\nThis wiki entry for **{self.name}** is currently being populated with information from available sources."
        return self.write_content(placeholder_content, is_placeholder=True)

    def get_url_path(self) -> str:
        """Get the URL path for this wiki entry"""
        return f"/wiki/{self.filename}"


def extract_wiki_items(text: str) -> List[Tuple[str, str]]:
    """
    Extract items in brackets from text and categorize them.

    Returns:
        List of tuples (item_name, category)
    """
    # Pattern to match text in brackets
    pattern = r'\[([^\]]+)\]'
    matches = re.findall(pattern, text)

    items = []
    for match in matches:
        item_name = match.strip()
        if not item_name:
            continue

        # Skip if it looks like a hexagram reference
        if re.match(r'^\d+[\:\-]', item_name) or item_name.lower().startswith('hexagram'):
            continue

        # Categorize the item
        category = categorize_item(item_name)
        items.append((item_name, category))

    return items


def categorize_item(item_name: str) -> str:
    """
    Categorize an item into characters, events, places, or concepts.

    This is a heuristic-based categorization with specific knowledge for common topics.
    """
    item_lower = item_name.lower()

    # Specific known events (case-insensitive)
    known_events = ['ragnarok', 'ragnarök', 'battle of ragnarok', 'twilight of the gods', 'armageddon', 'apocalypse', 'creation', 'genesis']
    if any(event in item_lower for event in known_events):
        return "events"

    # Specific known places (case-insensitive)
    known_places = ['asgard', 'midgard', 'valhalla', 'bifrost', 'yggdrasil', 'helheim', 'jotunheim', 'alfheim', 'vanaheim', 'nidavellir', 'muspelheim', 'niflheim']
    if any(place in item_lower for place in known_places):
        return "places"

    # Specific known concepts (case-insensitive)
    known_concepts = ['wyrd', 'fate', 'destiny', 'karma', 'dharma', 'tao', 'chi', 'qi', 'yin yang', 'philosophy', 'doctrine', 'principle', 'theory', 'belief', 'practice', 'method', 'art', 'way']
    if any(concept in item_lower for concept in known_concepts):
        return "concepts"

    # Events often contain action words or dates
    event_keywords = ['battle', 'war', 'revolution', 'death', 'birth', 'founding', 'treaty', 'siege', 'campaign', 'revolt', 'invasion', 'conquest', 'ceremony', 'ritual', 'sacrifice', 'prophecy', 'end times', 'judgment']
    if any(keyword in item_lower for keyword in event_keywords):
        return "events"

    # Places often contain geographical indicators
    place_keywords = ['city', 'kingdom', 'empire', 'river', 'mountain', 'forest', 'temple', 'palace', 'land', 'island', 'realm', 'world', 'bridge', 'tree', 'hall', 'well', 'spring']
    if any(keyword in item_lower for keyword in place_keywords):
        return "places"

    # Concepts often contain abstract terms
    concept_keywords = ['philosophy', 'doctrine', 'principle', 'theory', 'belief', 'practice', 'method', 'art', 'way', 'magic', 'spell', 'curse', 'blessing', 'power', 'energy', 'force', 'element']
    if any(keyword in item_lower for keyword in concept_keywords):
        return "concepts"

    # Default to characters for named entities
    return "characters"


def load_synonyms() -> Dict[str, Dict[str, str]]:
    """
    Load synonyms from the synonyms.json file.

    Returns:
        Dictionary mapping synonym names to their canonical entries
    """
    try:
        if SYNONYMS_FILE.exists():
            with open(SYNONYMS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading synonyms: {e}")
    return {}


def resolve_synonym(name: str) -> Tuple[str, str]:
    """
    Resolve a name to its canonical form, checking for synonyms.

    Args:
        name: The name to resolve

    Returns:
        Tuple of (canonical_name, category) - returns original if no synonym found
    """
    synonyms = load_synonyms()

    # Create filename from name for lookup
    filename = WikiEntry(name)._create_filename(name)

    if filename in synonyms:
        canonical_info = synonyms[filename]
        canonical_name = canonical_info['canonical'].replace('_', ' ').title()
        category = canonical_info['category']
        return canonical_name, category

    # Return original if no synonym found
    return name, categorize_item(name)


def create_wiki_links(text: str) -> str:
    """
    Replace bracketed items with wiki links and create placeholder entries.

    Args:
        text: The text to process

    Returns:
        Text with wiki links
    """
    # Extract wiki items
    items = extract_wiki_items(text)

    # Create placeholders for new items (resolve synonyms first)
    for item_name, category in items:
        canonical_name, canonical_category = resolve_synonym(item_name)
        entry = WikiEntry(canonical_name, canonical_category)
        if not entry.exists():
            entry.create_placeholder()

    # Replace bracketed items with links
    def replace_bracket_with_link(match):
        item_name = match.group(1).strip()

        # Skip hexagram references
        if re.match(r'^\d+[\:\-]', item_name) or item_name.lower().startswith('hexagram'):
            return match.group(0)

        # Resolve synonyms to get canonical name and category
        canonical_name, category = resolve_synonym(item_name)
        entry = WikiEntry(canonical_name, category)
        return f'<a href="{entry.get_url_path()}" class="wiki-link">{item_name}</a>'

    # Replace all bracketed items
    pattern = r'\[([^\]]+)\]'
    enhanced_text = re.sub(pattern, replace_bracket_with_link, text)

    return enhanced_text


async def populate_wiki_entry_from_wikipedia(entry: WikiEntry) -> bool:
    """
    Populate a wiki entry from Wikipedia asynchronously.

    Args:
        entry: The WikiEntry to populate

    Returns:
        True if successful, False otherwise
    """
    try:
        # Wikipedia API search
        search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(entry.name)}"

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract the summary
                    title = data.get('title', entry.name)
                    extract = data.get('extract', '')

                    if extract:
                        # Create content from Wikipedia summary
                        content = f"## Overview\n\n{extract}\n\n"

                        # Add source attribution
                        content += f"*Source: [Wikipedia]({data.get('content_urls', {}).get('desktop', {}).get('page', '')})*"

                        # Write the content
                        return entry.write_content(content)

    except Exception as e:
        print(f"Error fetching Wikipedia data for {entry.name}: {e}")

    return False


async def populate_wiki_entry_from_chatgpt(entry: WikiEntry) -> bool:
    """
    Populate a wiki entry using ChatGPT asynchronously.

    Args:
        entry: The WikiEntry to populate

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create a prompt for ChatGPT
        prompt = f"""
        Please provide a comprehensive but concise overview of "{entry.name}".

        Include:
        - A brief description of who/what they are
        - Their historical or mythological significance
        - Key attributes, achievements, or characteristics
        - Any relevant cultural or religious associations

        Format your response in markdown with an "Overview" section.
        Keep it informative but accessible, suitable for someone learning about this topic.
        Do not include external links or citations.
        """

        system_prompt = """
        You are a knowledgeable encyclopedia writer. Provide accurate, concise, and well-structured information about historical figures, mythological characters, events, places, and concepts. Focus on the most important and interesting aspects that would be useful for someone learning about the topic.
        """

        # Generate content using the existing LLM function
        content = generate_text_with_llm(
            system_prompt=system_prompt,
            user_prompt=prompt,
            temperature=0.3,  # Lower temperature for more factual content
            max_tokens=800
        )

        if content and content.strip():
            # Add source attribution
            content += f"\n\n*Generated by AI on {datetime.now().strftime('%Y-%m-%d')}*"

            # Write the content
            return entry.write_content(content)

    except Exception as e:
        print(f"Error generating AI content for {entry.name}: {e}")

    return False


async def populate_wiki_entry(entry: WikiEntry) -> bool:
    """
    Populate a wiki entry, trying Wikipedia first, then ChatGPT.

    Args:
        entry: The WikiEntry to populate

    Returns:
        True if successful, False otherwise
    """
    # Try Wikipedia first
    if await populate_wiki_entry_from_wikipedia(entry):
        return True

    # Fall back to ChatGPT
    return await populate_wiki_entry_from_chatgpt(entry)


def schedule_wiki_population(text: str) -> None:
    """
    Schedule async population of wiki entries found in text.
    Uses threading to avoid blocking the Flask app.

    Args:
        text: The text to scan for wiki items
    """
    items = extract_wiki_items(text)

    # Filter items that need population
    items_to_populate = []
    for item_name, category in items:
        entry = WikiEntry(item_name, category)
        if entry.is_placeholder():
            items_to_populate.append((item_name, category))

    if not items_to_populate:
        return

    # Create async task for each item that needs population
    async def populate_items():
        successful_count = 0
        for item_name, category in items_to_populate:
            try:
                entry = WikiEntry(item_name, category)
                result = await populate_wiki_entry(entry)
                if result:
                    successful_count += 1
                    print(f"✅ Populated wiki entry: {item_name} ({category})")
                else:
                    print(f"❌ Failed to populate: {item_name} ({category})")
            except Exception as e:
                print(f"❌ Error populating {item_name}: {e}")

        print(f"Wiki population completed: {successful_count}/{len(items_to_populate)} entries populated")

    # Schedule the async task in a background thread
    import threading

    def run_population():
        try:
            asyncio.run(populate_items())
        except Exception as e:
            print(f"Error in background wiki population: {e}")

    # Start in background thread
    thread = threading.Thread(target=run_population, daemon=True)
    thread.start()
    print(f"Scheduled background population for {len(items_to_populate)} wiki entries")


def populate_wiki_placeholders_sync() -> int:
    """
    Synchronously populate all placeholder wiki entries.

    Returns:
        Number of entries successfully populated
    """
    import asyncio

    async def populate_all():
        # Find all placeholder entries
        categories = ["characters", "events", "places", "concepts", "divination_types"]
        placeholders = []

        for category in categories:
            category_path = WIKI_DIR / category
            if category_path.exists():
                for md_file in category_path.glob("*.md"):
                    name = md_file.stem
                    entry = WikiEntry(name, category)
                    if entry.is_placeholder():
                        placeholders.append((name, category))

        print(f"Found {len(placeholders)} placeholder entries to populate")

        # Populate each one
        successful_count = 0
        for name, category in placeholders:
            try:
                entry = WikiEntry(name, category)
                result = await populate_wiki_entry(entry)
                if result:
                    successful_count += 1
                    print(f"✅ Populated: {name} ({category})")
                else:
                    print(f"❌ Failed: {name} ({category})")
            except Exception as e:
                print(f"❌ Error populating {name}: {e}")

        return successful_count

    # Run the async function
    return asyncio.run(populate_all())


def get_wiki_entry_content(filename: str) -> Optional[Tuple[str, str]]:
    """
    Get the content of a wiki entry by filename, searching across all categories.
    Also handles synonym resolution.

    Args:
        filename: The filename (without .md extension)

    Returns:
        Tuple of (content_html, category) if found, None if not found
    """
    categories = ["characters", "events", "places", "concepts", "divination_types"]

    # First, try to find the file directly
    for category in categories:
        filepath = WIKI_DIR / category / f"{filename}.md"

        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Convert markdown to HTML
                    html_content = markdown.markdown(content)
                    return html_content, category
            except Exception as e:
                print(f"Error reading wiki entry {filepath}: {e}")

    # If not found, check if it's a synonym
    synonyms = load_synonyms()
    if filename in synonyms:
        canonical_info = synonyms[filename]
        canonical_filename = canonical_info['canonical']
        canonical_category = canonical_info['category']

        # Try to get the canonical entry
        canonical_filepath = WIKI_DIR / canonical_category / f"{canonical_filename}.md"
        if canonical_filepath.exists():
            try:
                with open(canonical_filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Convert markdown to HTML
                    html_content = markdown.markdown(content)
                    return html_content, canonical_category
            except Exception as e:
                print(f"Error reading canonical wiki entry {canonical_filepath}: {e}")

    return None


def list_wiki_entries(category: Optional[str] = None) -> Dict[str, List[str]]:
    """
    List all wiki entries, optionally filtered by category.

    Args:
        category: Optional category to filter by

    Returns:
        Dictionary with categories as keys and lists of filenames as values
    """
    entries = {}

    categories = [category] if category else ["characters", "events", "places", "concepts", "divination_types"]

    for cat in categories:
        cat_dir = WIKI_DIR / cat
        if cat_dir.exists():
            entries[cat] = []
            for file in cat_dir.glob("*.md"):
                entries[cat].append(file.stem)

    return entries


def add_synonym(synonym_name: str, canonical_name: str, category: str) -> bool:
    """
    Add a new synonym to the synonyms file.

    Args:
        synonym_name: The synonym name
        canonical_name: The canonical entry name
        category: The category of the canonical entry

    Returns:
        True if successful, False otherwise
    """
    try:
        synonyms = load_synonyms()

        # Create filename from synonym name
        synonym_filename = WikiEntry(synonym_name)._create_filename(synonym_name)
        canonical_filename = WikiEntry(canonical_name)._create_filename(canonical_name)

        # Add the synonym
        synonyms[synonym_filename] = {
            'canonical': canonical_filename,
            'category': category
        }

        # Save back to file
        with open(SYNONYMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(synonyms, f, indent=4, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"Error adding synonym: {e}")
        return False


def remove_synonym(synonym_name: str) -> bool:
    """
    Remove a synonym from the synonyms file.

    Args:
        synonym_name: The synonym name to remove

    Returns:
        True if successful, False otherwise
    """
    try:
        synonyms = load_synonyms()

        # Create filename from synonym name
        synonym_filename = WikiEntry(synonym_name)._create_filename(synonym_name)

        if synonym_filename in synonyms:
            del synonyms[synonym_filename]

            # Save back to file
            with open(SYNONYMS_FILE, 'w', encoding='utf-8') as f:
                json.dump(synonyms, f, indent=4, ensure_ascii=False)

            return True
        else:
            print(f"Synonym '{synonym_name}' not found")
            return False

    except Exception as e:
        print(f"Error removing synonym: {e}")
        return False


def list_synonyms() -> Dict[str, Tuple[str, str]]:
    """
    List all synonyms with their canonical entries.

    Returns:
        Dictionary mapping synonym names to (canonical_name, category) tuples
    """
    synonyms = load_synonyms()
    result = {}

    for synonym_filename, info in synonyms.items():
        synonym_name = synonym_filename.replace('_', ' ').title()
        canonical_name = info['canonical'].replace('_', ' ').title()
        category = info['category']
        result[synonym_name] = (canonical_name, category)

    return result
